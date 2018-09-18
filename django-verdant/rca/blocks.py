from django.db.models import Min

from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.models import Page
from wagtail.wagtailembeds import blocks as embed_blocks
from wagtail.wagtailimages import blocks as image_blocks


class ShowcaseBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    pages = blocks.StreamBlock([(
        'Page', blocks.PageChooserBlock()
    )])

    class Meta:
        icon = 'list-ul'
        template = 'rca/blocks/showcase_block.html'

    def get_context(self, value):
        context = super(ShowcaseBlock, self).get_context(value)
        context['showcase_pages'] = [
            child.value.specific for child in value['pages']
        ]
        return context


class VideoBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    video = embed_blocks.EmbedBlock()
    poster_image = image_blocks.ImageChooserBlock(required=False)

    class Meta:
        icon = 'media'
        template = 'rca/blocks/video_block.html'


class TestimonialBlock(blocks.StructBlock):
    image = image_blocks.ImageChooserBlock()
    quote = blocks.CharBlock()
    further_description = blocks.CharBlock(required=False)
    reference = blocks.CharBlock(required=False)

    class Meta:
        template = 'rca/blocks/testimonial_block.html'


class TestimonialsBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    testimonials = blocks.StreamBlock([(
        'Testimonial', TestimonialBlock()
    )])

    class Meta:
        icon = 'group'
        template = 'rca/blocks/testimonials_block.html'


class NewsBlock(blocks.StructBlock):
    featured_page = blocks.PageChooserBlock()
    more_news_link = blocks.PageChooserBlock()

    def get_context(self, value):
        from rca.models import NewsItem, PressRelease, RcaBlogPage
        context = super(NewsBlock, self).get_context(value)
        pages = Page.objects.type(NewsItem) | Page.objects.type(PressRelease) \
            | Page.objects.type(RcaBlogPage)
        pages = pages.not_page(value['featured_page']).specific()
        context['pages'] = sorted(
            pages, key=lambda p: p.date, reverse=True
        )[:4]
        return context

    class Meta:
        icon = 'list-ul'
        template = 'rca/blocks/news_block.html'


class EventsBlock(blocks.StructBlock):
    more_events_link = blocks.PageChooserBlock()

    def get_context(self, value):
        from rca.models import EventItem
        context = super(EventsBlock, self).get_context(value)
        context['events'] = EventItem.future_objects.live() \
            .annotate(start_date=Min('dates_times__date_from')) \
            .order_by('start_date')
        return context

    class Meta:
        icon = 'date'
        template = 'rca/blocks/events_block.html'


class HomepageBody(blocks.StreamBlock):
    showcase = ShowcaseBlock()
    video = VideoBlock()
    testimonials = TestimonialsBlock()
    news = NewsBlock()
    events = EventsBlock()
