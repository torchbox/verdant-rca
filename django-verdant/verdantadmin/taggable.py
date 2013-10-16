from taggit.models import Tag
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class TagSearchable(object):
    """
    Mixin to provide a 'search' method, searching on the 'title' field and tags,
    for models that provide those things.
    """

    search_on_fields = ['title']

    @classmethod
    def search(cls, q, results_per_page=None, page=1, prefetch_tags=False):
        terms = q.split()
        if not terms:
            return cls.objects.none()

        # in order to match, a result must contain ALL the given terms -
        # either as a tag beginning with that term, or within one of the fields named in search_on_fields
        search_query = None
        for term in terms:
            term_query = Q(tags__name__istartswith=term)
            for field_name in cls.search_on_fields:
                field_filter = {'%s__icontains' % field_name: term}
                term_query |= Q(**field_filter)

            if search_query is None:
                search_query = term_query
            else:
                search_query &= term_query

        results = cls.objects.filter(search_query).distinct()
        if prefetch_tags:
            results = results.prefetch_related('tagged_items__tag')

        # if results_per_page is set, return a paginator
        if results_per_page is not None:
            paginator = Paginator(results, results_per_page)
            try:
                return paginator.page(page)
            except PageNotAnInteger:
                return paginator.page(1)
            except EmptyPage:
                return paginator.page(paginator.num_pages)
        else:
            return results

    def prefetched_tags(self):
        # a hack to do the equivalent of self.tags.all() but take advantage of the
        # prefetch_related('tagged_items__tag') in the above search method, so that we can
        # output the list of tags on each result without doing a further query
        return [tagged_item.tag for tagged_item in self.tagged_items.all()]


    @classmethod
    def popular_tags(cls):
        content_type = ContentType.objects.get_for_model(cls)
        return Tag.objects.filter(
            taggit_taggeditem_items__content_type=content_type
        ).annotate(
            item_count=Count('taggit_taggeditem_items')
        ).order_by('-item_count')[:10]
