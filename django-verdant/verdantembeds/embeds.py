from datetime import datetime
from django.conf import settings
from embedly import Embedly
from .models import SavedEmbed


USER_AGENT = 'Mozilla/5.0 (compatible; django-embedly/0.2; ' \
        '+http://github.com/BayCitizen/)'


def get_embed(url, maxwidth=None):
    # Check database
    try:
        saved_embed = SavedEmbed.objects.get(url=url, maxwidth=maxwidth)
        return {
            'url': url,
            'maxwidth': maxwidth,
            'type': saved_embed.type,
            'title': saved_embed.title,
            'thumbnail_url': saved_embed.thumbnail_url,
            'html': saved_embed.html,
            'width': saved_embed.width,
            'height': saved_embed.height,
        }
    except SavedEmbed.DoesNotExist:
        pass

    # Call embedly API
    client = Embedly(key=settings.EMBEDLY_KEY, user_agent=USER_AGENT)
    if maxwidth:
        oembed = client.oembed(url, maxwidth=maxwidth)
    else:
        oembed = client.oembed(url)

    # Check for error
    if oembed.error:
        return None

    # Save result to database
    row, created = SavedEmbed.objects.get_or_create(url=url, maxwidth=maxwidth,
                defaults={'type': oembed.type, 'title': oembed.title, 'thumbnail_url': oembed.thumbnail_url, 'width': oembed.width, 'height': oembed.height})

    if oembed.type == 'photo':
        html = '<img src="%s" width="%s" height="%s" />' % (oembed.url,
                oembed.width, oembed.height)
    else:
        html = oembed.html

    if html:
        row.html = html
        row.last_updated = datetime.now()
        row.save()

    # Return new dictionary
    return {
        'url': url,
        'maxwidth': maxwidth,
        'title': oembed.title,
        'thumbnail_url': oembed.thumbnail_url,
        'type': oembed.type,
        'html': html,
        'width': oembed.width,
        'height': oembed.height,
    }