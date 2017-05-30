from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel

from rca.models import StaffPage
from rca.utils.models import SocialFields


# TODO: Move StaffPage, StaffIndexPage and all related models here


class ExpertsIndexPage(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True,
                                    help_text="Replace the default Twitter feed by providing an alternative "
                                              "Twitter handle (without the @ symbol)")
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                                   help_text="The image displayed in content feeds, such as the news carousel. "
                                             "Should be 16:9 ratio.")
    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        FieldPanel('twitter_feed'),
    ]

    promote_panels = [
        MultiFieldPanel([
            FieldPanel('seo_title'),
            FieldPanel('slug'),
        ], 'Common page configuration'),

        MultiFieldPanel([
            FieldPanel('show_in_menus'),
            ImageChooserPanel('feed_image'),
            FieldPanel('search_description'),
        ], 'Cross-page behaviour'),

        MultiFieldPanel([
            ImageChooserPanel('social_image'),
            FieldPanel('social_text'),
        ], 'Social networks'),
    ]

    def get_context(self, request, *args, **kwargs):
        query_string = request.GET.get('q')

        staff_pages = StaffPage.objects.live().public()
        # TODO: Uncomment once is_expert field is added to the StaffPage model
        # staff_pages = staff_pages.filter('is_expert')

        # TODO: Implement filtering

        if query_string:
            staff_pages = staff_pages.search(query_string, operator='and')

        # Paginate
        paginator = Paginator(staff_pages, 20)
        try:
            staff_pages = paginator.page(request.GET.get('p'))
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            staff_pages = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            staff_pages = paginator.page(paginator.num_pages)

        context = super(ExpertsIndexPage, self).get_context(request, *args, **kwargs)
        context.update({
            'search_results': staff_pages,
            'query_string': query_string,
        })

        return context
