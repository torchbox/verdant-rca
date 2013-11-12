from __future__ import division # Use true division
from django_embedly.templatetags.embed_filters import embedly_get_dict
from verdantimages.models import get_image_model


def media_to_frontend_html(url, poster_image_id=None):
    embed = embedly_get_dict(url)
    if embed is not None:
        # Work out ratio
        if embed['width'] and embed['height']:
            ratio = str(embed['height'] / embed['width'] * 100) + '%'
        else:
            ratio = '0'

        # If poster image id is set, add poster image
        if poster_image_id is not None and poster_image_id != 'None':
            # Get image
            image = get_image_model().objects.get(pk=poster_image_id)
            rendition = image.get_rendition('width-' + str(embed['width']))

            return '''
             <div class="videoembed vimeo responsive-object" style="padding-bottom: %s;">
              <div class="playpause play">Play</div>
              <div class="poster">%s</div>
              %s
             </div>''' % (ratio, rendition.img_tag(), embed['html'])
        else:
            return '<div style="padding-bottom: %s;" class="responsive-object">%s</div>' % (ratio, embed['html'])
    else:
        return ''


def media_to_editor_html(url, poster_image_id=None):
    # Check that the media exists
    embed = embedly_get_dict(url)
    if embed is None:
        return ''
    return '<div class="media-placeholder" contenteditable="false" data-embedtype="media" data-url="%s" data-poster-image-id="%s"><h3>%s</h3><p>%s</p><img src="%s"></div>' % (url, poster_image_id, embed['title'], url, embed['thumbnail_url'])