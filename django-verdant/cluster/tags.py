from taggit.managers import TaggableManager, _TaggableManager
from taggit.utils import require_instance_manager

from cluster.queryset import FakeQuerySet

class _ClusterTaggableManager(_TaggableManager):
    @require_instance_manager
    def get_tagged_item_manager(self):
        """Return the manager that handles the relation from this instance to the tagged_item class.
        If content_object on the tagged_item class is defined as a ParentalKey, this will be a
        DeferringRelatedManager which allows writing related objects without committing them
        to the database.
        """
        rel_name = self.through._meta.get_field('content_object').related.get_accessor_name()
        return getattr(self.instance, rel_name)

    def get_query_set(self):
        return FakeQuerySet(
            self.through.tag_model(),
            [tagged_item.tag for tagged_item in self.get_tagged_item_manager().all()]
        )

    # Django 1.6 renamed this
    get_queryset = get_query_set

    @require_instance_manager
    def add(self, *tags):
        # First turn the 'tags' list (which may be a mixture of tag objects and
        # strings which may or may not correspond to existing tag objects)
        # into 'tag_objs', a set of tag objects
        str_tags = set([
            t
            for t in tags
            if not isinstance(t, self.through.tag_model())
        ])
        tag_objs = set(tags) - str_tags
        # If str_tags has 0 elements Django actually optimizes that to not do a
        # query.  Malcolm is very smart.
        existing = self.through.tag_model().objects.filter(
            name__in=str_tags
        )
        tag_objs.update(existing)

        for new_tag in str_tags - set(t.name for t in existing):
            tag_objs.add(self.through.tag_model().objects.create(name=new_tag))

        # Now write these to the relation
        tagged_item_manager = self.get_tagged_item_manager()
        for tag in tag_objs:
            if not tagged_item_manager.filter(tag=tag):
                # make an instance of the self.through model and add it to the relation
                tagged_item = self.through(tag=tag)
                tagged_item_manager.add(tagged_item)

class ClusterTaggableManager(TaggableManager):
    def __get__(self, instance, model):
        # override TaggableManager's requirement for instance to have a primary key
        # before we can access its tags
        manager = _ClusterTaggableManager(
            through=self.through, model=model, instance=instance
        )
        return manager
