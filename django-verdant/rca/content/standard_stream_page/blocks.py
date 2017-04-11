from wagtail.wagtailadmin import blocks
from wagtail.wagtailcore.blocks import PageChooserBlock
from wagtail.wagtailembeds.blocks import EmbedBlock
from wagtail.wagtailimages.blocks import ImageChooserBlock


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    overlay_text = blocks.CharBlock(max_length=255, required=False)

    class Meta:
        icon = "image"
        template = "standard_stream_page/blocks/image_block.html"


class QuoteBlock(blocks.StructBlock):
    quotation = blocks.CharBlock(classname="title")
    quotee = blocks.CharBlock(max_length=255, required=False)
    quotee_job_title = blocks.CharBlock(max_length=255, required=False)
    image = ImageChooserBlock(required=False)

    position = blocks.ChoiceBlock(choices=(
        ('full', 'Full-width'),
        ('right', 'Right'),
    ), default='full')

    class Meta:
        icon = "openquote"
        template = "standard_stream_page/blocks/quote_block.html"


class CalloutBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=255)
    text = blocks.TextBlock()
    link_page = PageChooserBlock()
    image = ImageChooserBlock(required=False)

    class Meta:
        icon = "view"
        template = "standard_stream_page/blocks/callout_block.html"


class CarouselItemBlock(blocks.StructBlock):
    image = ImageBlock()
    link = blocks.URLBlock(required=False, label="External link")
    link_page = PageChooserBlock(required=False)

    def get_context(self, value):
        item_link = value['link_page'].url if value.get('link_page') else value['link']

        context = super(CarouselItemBlock, self).get_context(value)
        context.update({
            'item_link': item_link,
        })
        return context

    class Meta:
        template = "standard_stream_page/blocks/carousel_item_block.html"


class StandardStreamBlock(blocks.StreamBlock):
    paragraph = blocks.RichTextBlock()
    image = ImageBlock()
    quote = QuoteBlock()
    embed = EmbedBlock()
    callout = CalloutBlock()
    carousel = blocks.ListBlock(
        CarouselItemBlock(),
        template="standard_stream_page/blocks/carousel_block.html"
    )

    class Meta:
        template = "standard_stream_page/blocks/stream_block.html"
