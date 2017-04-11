from wagtail.wagtailadmin import blocks
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


class StandardStreamBlock(blocks.StreamBlock):
    paragraph = blocks.RichTextBlock()
    image = ImageBlock()
    quote = QuoteBlock()
    embed = EmbedBlock()
    # TODO: carousel
    # TODO: Right-hand callout block

    class Meta:
        template = "standard_stream_page/blocks/stream_block.html"
