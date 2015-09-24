import time
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.utils.http import http_date

from . import tasks
from .models import Tweet


def statuses_user_timeline(request):
    if not settings.TWITTER_CONSUMER_KEY:
        return HttpResponse("[]", content_type="application/json")

    callback = request.GET.get("callback")
    screen_name = request.GET.get("screen_name", "RCAevents").strip().strip('@')
    count = int(request.GET.get("count", 10))
    cache_key = "tweets_from_%s_last_%s" % (slugify(screen_name), count)
    result = cache.get(cache_key)

    tweets_for_screen_name = Tweet.objects.filter(user_screen_name__iexact=screen_name).order_by('-created_at')

    tweets_for_screen_name_exist_cache_key = "tweets_for_screen_name_exist_%s" % (slugify(screen_name))
    tweets_for_screen_name_exist = cache.get(tweets_for_screen_name_exist_cache_key)
    if not tweets_for_screen_name_exist:
        tweets_for_screen_name_exist = tweets_for_screen_name.exists()
        cache.set(tweets_for_screen_name_exist_cache_key, tweets_for_screen_name_exist, settings.CELERYBEAT_CACHE_MED_TIME)

    if not tweets_for_screen_name_exist:
        # no tweets in the database -> fetch some ASAP (but with a long delay between retries)
        # on the next request the tweets will be there
        cache_key_initial = "tweets_from_%s_initial" % slugify(screen_name)
        if not cache.get(cache_key_initial):
            tasks.get_tweets(screen_name, count)
            tweets_for_screen_name = Tweet.objects.filter(user_screen_name__iexact=screen_name).order_by('-created_at')
            tweets_for_screen_name_exist = tweets_for_screen_name.exists()
            cache.set(cache_key_initial, True, settings.CELERYBEAT_CACHE_MED_TIME)

    if not result and tweets_for_screen_name_exist:
        # we have some records in the databse already but nothing in the cache -> execute db query
        result = '[%s]' % ",\n ".join(map(lambda e: e[0], list(tweets_for_screen_name[:count].values_list("payload"))))
        cache.set(cache_key, result, settings.CELERYBEAT_CACHE_SHORT_TIME)

    if callback:
        result = "%s(%s)" % (callback, result or "[]")

    response = HttpResponse(result or "[]", content_type="application/json")
    # tell the browser and / or reverse proxy to cache this response
    response['Expires'] = http_date(time.time() + settings.CELERYBEAT_CACHE_SHORT_TIME)

    return response
