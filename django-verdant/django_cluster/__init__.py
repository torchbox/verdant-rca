# example usage:

# from rca.models import NewsItem, NewsItemLink
# from django_cluster import build_clusterable_model

# ClusterableNewsItem = build_clusterable_model(NewsItem, {'related_links': NewsItemLink})
# ni = ClusterableNewsItem(title='test', related_links=[{'link': 'http://torchbox.com'}])
# ni.related_links.all()

from django_cluster.queryset import FakeQuerySet
from django.db import models
from django.utils.functional import cached_property


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
                if item not in items:
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

    return DeferringRelatedManager

class DeferringForeignRelatedObjectsDescriptor(object):
    """
    Wrapper for a ForeignRelatedObjectsDescriptor so that accesses to an incoming
    foreign key attribute on a model are directed to a DeferringRelatedManager
    rather than a plain RelatedManager. This ensures that writes to that attribute
    are stored locally rather than committed to the database immediately.
    """
    def __init__(self, original_descriptor):
        self.original_descriptor = original_descriptor

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        return self.deferring_related_manager_cls(instance)

    def __set__(self, instance, value):
        manager = self.__get__(instance)
        manager.clear()
        manager.add(*value)

    @cached_property
    def deferring_related_manager_cls(self):
        return create_deferring_foreign_related_manager(
            self.original_descriptor.related.get_accessor_name(),
            self.original_descriptor.related_manager_cls
        )


def build_clusterable_model(model, overrides):
    """
    Construct a tweaked version of the 'model' class, adding deferring behaviour
    to the foreign key relations named in the dict 'overrides'. Each key-value pair
    in 'overrides' specifies a relation name to override, mapped to the model class
    that this should be a collection of. (This class isn't necessarily the same as
    the model class of the original relation; it may itself be a tweaked version
    constructed using this function.)
    """
    if not overrides:
        # no overriding of the original model is necessary
        return model

    Meta = type('Meta', (), {'proxy': True, 'app_label': 'django_cluster'})

    def init(self, *args, **kwargs):
        """
        Model instance constructor, extended to support passing in kwargs for
        deferring relations. Each such kwarg is a list of dicts, each one being
        the kwargs to pass to the related model's constructor.
        """
        kwargs_for_super = kwargs.copy()
        relation_assignments = {}

        for (field_name, related_model) in overrides.items():
            try:
                field_val = kwargs_for_super.pop(field_name)
            except KeyError:
                continue

            related_instances = [
                related_model(**field_dict)
                for field_dict in field_val
            ]
            relation_assignments[field_name] = related_instances

        super(cls, self).__init__(*args, **kwargs_for_super)

        for (field_name, related_instances) in relation_assignments.items():
            setattr(self, field_name, related_instances)

    def save(self, **kwargs):
        """
        Save the model and commit all deferring relations.
        """
        update_fields = kwargs.pop('update_fields', None)
        if update_fields is None:
            real_update_fields = None
            relations_to_commit = list(overrides)
        else:
            real_update_fields = []
            relations_to_commit = []
            for field in update_fields:
                if field in overrides:
                    relations_to_commit.append(field)
                else:
                    real_update_fields.append(field)

        super(cls, self).save(update_fields=real_update_fields, **kwargs)

        for relation in relations_to_commit:
            getattr(self, relation).commit()

    dct = {
        'clusterable_relations': overrides,
        'Meta': Meta,
        '__module__': 'django_cluster.models',
        '__init__': init,
        'save': save,
    }
    for name in overrides:
        original_descriptor = getattr(model, name)
        dct[name] = DeferringForeignRelatedObjectsDescriptor(original_descriptor)

    cls = type('Clusterable%s' % model.__name__, (model,), dct)
    return cls
