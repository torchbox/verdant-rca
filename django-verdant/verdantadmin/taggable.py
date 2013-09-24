from taggit.models import Tag

class TagSearchable(object):
    """
    Mixin to provide a 'search' method, searching on the 'title' field and tags,
    for models that provide those things.
    """

    @classmethod
    def search(cls, q):
        # TODO: speed up this search - currently istartswith is doing sequential scan
        strings = q.split()
        # match according to tags first
        tags = Tag.objects.none()
        for string in strings:
            tags = tags | Tag.objects.filter(name__startswith=string)
        # NB the following line will select images if any tags match, not just if all do
        tag_matches = cls.objects.filter(tags__in = tags).distinct()
        # now match according to titles
        title_matches = cls.objects.none()
        results = cls.objects.all()
        for term in strings:
            title_matches = title_matches | results.filter(title__istartswith=term).distinct()
        results = tag_matches | title_matches
        return results
