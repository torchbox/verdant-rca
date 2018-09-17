from wagtail.wagtailcore import blocks


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


class HomepageBody(blocks.StreamBlock):
    showcase = ShowcaseBlock()
