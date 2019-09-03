from .production import *

if 'MEDIA_URL' in env:
    MEDIA_URL = env['MEDIA_URL']

    # HACK: MEDIA_URL should include scheme and domain name so that URLs generate for the video embed on StreamPage work
    if MEDIA_URL.startswith('/'):
        MEDIA_URL = 'https://rca-staging.torchboxapps.com' + MEDIA_URL
