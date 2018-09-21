from django.core.exceptions import ValidationError
from django.db.models import Min
from django.forms.utils import ErrorList

from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.blocks.stream_block import StreamBlockValidationError
from wagtail.wagtailcore.blocks.struct_block import StructValue
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

    def clean(self, value):
        result = []
        errors = {}
        for name, val in value.items():
            try:
                result.append((name, self.child_blocks[name].clean(val)))

                # can be removed when updated to Wagtail 1.12 or above
                # https://docs.wagtail.io/en/v1.12.6/topics/streamfield.html#streamblock
                if name == 'pages' and len(val) < 5:
                    raise StreamBlockValidationError(
                        non_block_errors=['Please choose a minumum of 5 pages']
                    )
            except ValidationError as e:
                errors[name] = ErrorList([e])

        if errors:
            raise ValidationError(
                'Validation error in StructBlock', params=errors)

        return StructValue(self, result)

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
        pages = pages.not_page(value['featured_page']).live().specific()
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


class TwoColumnBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    column_one_image = image_blocks.ImageChooserBlock()
    column_one_link_text = blocks.CharBlock()
    column_one_link_page = blocks.PageChooserBlock()
    column_two_image = image_blocks.ImageChooserBlock()
    column_two_link_text = blocks.CharBlock()
    column_two_link_page = blocks.PageChooserBlock()

    class Meta:
        icon = 'grip'
        template = 'rca/blocks/two_column_block.html'


class HomepageBody(blocks.StreamBlock):
    showcase = ShowcaseBlock(help_text='Please choose 5 pages')
    video = VideoBlock()
    testimonials = TestimonialsBlock()
    news = NewsBlock()
    events = EventsBlock()
    two_column_block = TwoColumnBlock()
