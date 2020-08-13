from django.core.exceptions import ValidationError
from wagtail.wagtailcore import blocks
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

    position = blocks.ChoiceBlock(choices=(
        ('full', 'Full-width quote block'),
        ('right', 'Right-hand quote block'),
    ), default='full')
    image = ImageChooserBlock(required=False, help_text="Can be used only in a full-width quote block")
    left_hand_text = blocks.RichTextBlock(required=False, help_text="Can be used only in a right-hand quote block")

    def clean(self, value):
        result = super(QuoteBlock, self).clean(value)
        errors = {}

        if value['position'] == 'full':
            if value['left_hand_text'].source != '':
                errors['left_hand_text'] = ValidationError(
                    "You can specify left-hand text only in a right-hand quote block"
                )
        elif value['position'] == 'right':
            if value['left_hand_text'].source == '':
                errors['left_hand_text'] = ValidationError("Left-hand text is required in a right-hand quote block")

            if value['image'] is not None:
                errors['image'] = ValidationError("An image can't be used in a right-hand quote block")

        if errors:
            raise ValidationError('Validation error in QuoteBlock', params=errors)

        return result

    class Meta:
        icon = "openquote"
        template = "standard_stream_page/blocks/quote_block.html"


class CalloutBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=255)
    text = blocks.TextBlock()
    link_page = PageChooserBlock()
    image = ImageChooserBlock(required=False)
    left_hand_text = blocks.RichTextBlock()

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
