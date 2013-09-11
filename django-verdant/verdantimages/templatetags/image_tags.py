from django import template

from verdantimages.models import Format

register = template.Library()

@register.tag(name="image")
def image(parser, token):
    args = token.split_contents()

    if len(args) == 3:
        # token is of the form {% image self.photo 320x200 %}
        tag_name, image_var, format_spec = args
        return ImageNode(image_var, format_spec)

    elif len(args) == 5:
        # token is of the form {% image self.photo 320x200 as img %}
        tag_name, image_var, format_spec, as_token, out_var = args

        if as_token != 'as':
            raise template.TemplateSyntaxError("'image' tag should be of the form {%% image self.photo 320x200 %%} or {%% image self.photo 320x200 as img %%}")

        return ImageNode(image_var, format_spec, out_var)

    else:
        raise template.TemplateSyntaxError("'image' tag should be of the form {%% image self.photo 320x200 %%} or {%% image self.photo 320x200 as img %%}")

class ImageNode(template.Node):
    def __init__(self, image_var_name, format_spec, output_var_name=None):
        self.image_var = template.Variable(image_var_name)
        self.format, created = Format.objects.get_or_create(spec=format_spec)
        self.output_var_name = output_var_name

    def render(self, context):
        try:
            image = self.image_var.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        if not image:
            return ''

        rendition = image.get_in_format(self.format)

        if self.output_var_name:
            # return the rendition object in the given variable
            context[self.output_var_name] = rendition
            return ''
        else:
            # render the rendition's image tag now
            return rendition.img_tag()
