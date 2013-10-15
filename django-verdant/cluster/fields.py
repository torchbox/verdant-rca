from django.db import models
from django.db.models.fields.related import ForeignKey, ForeignRelatedObjectsDescriptor
from django.utils.functional import cached_property

try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    # south is not in use, so make add_introspection_rules a no-op
    def add_introspection_rules(*args):
        pass

from cluster.queryset import FakeQuerySet


def create_deferring_foreign_related_manager(relation_name, original_manager_cls):
    """
    Create a DeferringRelatedManager class that wraps an ordinary RelatedManager
    with 'deferring' behaviour: any updates to the object set (via e.g. add() or clear())
    are written to a holding area rather than committed to the database immediately.
    Writing to the database is deferred until the model is saved.
    """
    class DeferringRelatedManager(models.Manager):
        def __init__(self, instance):
            self.instance = instance

        def get_live_query_set(self):
            """
            return the original manager's queryset, which reflects the live database
            """
            return original_manager_cls(self.instance).get_query_set()

        def get_query_set(self):
            """
            return the current object set with any updates applied,
            wrapped up in a FakeQuerySet if it doesn't match the database state
            """
            try:
                results = self.instance._cluster_related_objects[relation_name]
            except (AttributeError, KeyError):
                return self.get_live_query_set()

            return FakeQuerySet(*results)

        def add(self, *new_items):
            """
            Add the passed items to the stored object set, but do not commit them
            to the database
            """
            try:
                cluster_related_objects = self.instance._cluster_related_objects
            except AttributeError:
                cluster_related_objects = {}
                self.instance._cluster_related_objects = cluster_related_objects

            try:
                items = cluster_related_objects[relation_name]
            except KeyError:
                items = list(self.get_live_query_set())
                cluster_related_objects[relation_name] = items

            for item in new_items:
                # Check if item is already in the list. Can't do this with a simple 'in'
                # check due to https://code.djangoproject.com/ticket/18864
                item_exists = False
                for other in items:
                    if (item is other) or (item.pk == other.pk and item.pk is not None):
                        item_exists = True
                        break

                if not item_exists:
                    items.append(item)

        def clear(self):
            """
            Clear the stored object set, without affecting the database
            """
            try:
                cluster_related_objects = self.instance._cluster_related_objects
            except AttributeError:
                cluster_related_objects = {}
                self.instance._cluster_related_objects = cluster_related_objects

            cluster_related_objects[relation_name] = []

        def commit(self):
            """
            Apply any changes made to the stored object set to the database.
            Any objects removed from the initial set will be deleted entirely
            from the database.
            """
            try:
                final_items = self.instance._cluster_related_objects[relation_name]
            except (AttributeError, KeyError):
                # _cluster_related_objects entry never created => no changes to make
                return

            original_manager = original_manager_cls(self.instance)

            live_items = list(original_manager.get_query_set())
            for item in live_items:
                if item not in final_items:
                    item.delete()

            for item in final_items:
                if item not in live_items:
                    original_manager.add(item)
                else:
                    item.save()

            # purge the _cluster_related_objects entry, so we switch back to live SQL
            del self.instance._cluster_related_objects[relation_name]

    return DeferringRelatedManager


class ChildObjectsDescriptor(ForeignRelatedObjectsDescriptor):
    def __init__(self, related):
        super(ChildObjectsDescriptor, self).__init__(related)

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        return self.child_object_manager_cls(instance)

    def __set__(self, instance, value):
        manager = self.__get__(instance)
        manager.clear()
        manager.add(*value)

    @cached_property
    def child_object_manager_cls(self):
        return create_deferring_foreign_related_manager(
            self.related.get_accessor_name(),
            self.related_manager_cls
        )


class ParentalKey(ForeignKey):
    related_accessor_class = ChildObjectsDescriptor

    # prior to https://github.com/django/django/commit/fa2e1371cda1e72d82b4133ad0b49a18e43ba411
    # ForeignRelatedObjectsDescriptor is hard-coded in contribute_to_related_class -
    # so we need to patch in that change to look up related_accessor_class instead
    def contribute_to_related_class(self, cls, related):
        # Internal FK's - i.e., those with a related name ending with '+' -
        # and swapped models don't get a related descriptor.
        if not self.rel.is_hidden() and not related.model._meta.swapped:
            setattr(cls, related.get_accessor_name(), self.related_accessor_class(related))
            if self.rel.limit_choices_to:
                cls._meta.related_fkey_lookups.append(self.rel.limit_choices_to)
        if self.rel.field_name is None:
            self.rel.field_name = cls._meta.pk.name

        # store this as a child field in meta
        try:
            # TODO: figure out how model inheritance works with this
            cls._meta.child_relations.append(related)
        except AttributeError:
            cls._meta.child_relations = [related]

add_introspection_rules([], ["^cluster\.fields\.ParentalKey"])
