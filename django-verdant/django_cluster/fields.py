from django.db.models.fields.related import ForeignKey, ForeignRelatedObjectsDescriptor
from django.utils.functional import cached_property
from django_cluster import create_deferring_foreign_related_manager

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
