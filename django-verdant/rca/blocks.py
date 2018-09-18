from wagtail.wagtailcore import blocks
from wagtail.wagtailembeds import blocks as embed_blocks
from wagtail.wagtailimages.blocks import ImageChooserBlock


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
    poster_image = ImageChooserBlock(required=False)

    class Meta:
        icon = 'media'
        template = 'rca/blocks/video_block.html'


class HomepageBody(blocks.StreamBlock):
    showcase = ShowcaseBlock()
    video = VideoBlock()
