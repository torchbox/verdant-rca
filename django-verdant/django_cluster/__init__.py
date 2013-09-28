# example usage:

# from rca.models import NewsItem, NewsItemLink
# from django_cluster import build_clusterable_model

# ClusterableNewsItem = build_clusterable_model(NewsItem, {'related_links': NewsItemLink})
# ni = ClusterableNewsItem(title='test', related_links=[{'link': 'http://torchbox.com'}])
# ni.related_links.all()

from django_cluster.queryset import FakeQuerySet
from django.db import models
from django.utils.functional import cached_property


def create_deferring_foreign_related_manager(relation_name, rel_field, original_manager_cls):
    class DeferringRelatedManager(models.Manager):
        def __init__(self, instance):
            self.instance = instance

        def get_live_query_set(self):
            """
            return the original manager's queryset, which reflects the live database
            """
            return original_manager_cls(self.instance).get_query_set()

        def get_query_set(self):
            try:
                results = self.instance._cluster_related_objects[relation_name]
            except (AttributeError, KeyError):
                return self.get_live_query_set()

            return FakeQuerySet(*results)

        def add(self, *new_items):
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

        if rel_field.null:
            def clear(self):
                try:
                    cluster_related_objects = self.instance._cluster_related_objects
                except AttributeError:
                    cluster_related_objects = {}
                    self.instance._cluster_related_objects = cluster_related_objects

                cluster_related_objects[relation_name] = []

        def commit(self):
            # apply any changes present in _cluster_related_objects to the database
            try:
                final_items = self.instance._cluster_related_objects[relation_name]
            except (AttributeError, KeyError):
                # _cluster_related_objects entry never created => no changes to make
                return

            original_manager = original_manager_cls(self.instance)

            live_items = list(original_manager.get_query_set())
            items_to_remove = [
                item for item in live_items
                if item not in final_items
            ]

            if items_to_remove:
                # original_manager.remove() is only defined for nullable
                # foreign keys, but if that isn't the case, then the object
                # assignment logic here and in DeferringForeignRelatedObjectsDescriptor
                # should ensure that there are never items to remove.
                original_manager.remove(*items_to_remove)

            for item in final_items:
                if item not in live_items:
                    original_manager.add(item)
                else:
                    item.save()

    return DeferringRelatedManager

# wrapper for a ForeignRelatedObjectsDescriptor so that it exposes a DeferringRelatedManager
# rather than a plain RelatedManager
class DeferringForeignRelatedObjectsDescriptor(object):
    def __init__(self, original_descriptor):
        self.original_descriptor = original_descriptor

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        return self.deferring_related_manager_cls(instance)

    def __set__(self, instance, value):
        manager = self.__get__(instance)
        # If the foreign key can support nulls, then completely clear the related set.
        # Otherwise, just move the named objects into the set.
        if self.original_descriptor.related.field.null:
            manager.clear()
        manager.add(*value)

    @cached_property
    def deferring_related_manager_cls(self):
        return create_deferring_foreign_related_manager(
            self.original_descriptor.related.get_accessor_name(),
            self.original_descriptor.related.field,
            self.original_descriptor.related_manager_cls
        )


def build_clusterable_model(model, overrides):
    if not overrides:
        # no overriding of the original model is necessary
        return model

    Meta = type('Meta', (), {'proxy': True, 'app_label': 'django_cluster'})

    def init(self, *args, **kwargs):
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

    dct = {
        'Meta': Meta,
        '__module__': 'django_cluster.models',
        '__init__': init
    }
    for name in overrides:
        original_descriptor = getattr(model, name)
        dct[name] = DeferringForeignRelatedObjectsDescriptor(original_descriptor)

    cls = type('Clusterable%s' % model.__name__, (model,), dct)
    return cls
