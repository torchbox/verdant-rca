import random

import tweepy
from tweepy.error import TweepError

from django.conf import settings

from .models import Tweet


def get_api():
    # app level rate limit: 300 request every 15 minutes
    auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
    auth.set_access_token(settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())
    return api


def get_tweets(screen_name, count=10):
    api = get_api()

    count = min(count, 50)

    try:
        if api.get_user(screen_name=screen_name)["protected"]:
            return
    except TweepError:
        return  # ignore 404 errors

    try:
        data = api.rate_limit_status()  # {'remaining': 178, 'limit': 180, 'reset': 1459422554}
        remaining = data['resources']['statuses']['/statuses/user_timeline']['remaining']
        if remaining < 1:
            # we can't do anything now but users will trigger this again, and the new screen name will be added eventually
            return

        for status in api.user_timeline(screen_name=screen_name, exclude_replies=True, count=count):
            Tweet.save_from_dict(status)
            data = api.rate_limit_status()  # {'remaining': 178, 'limit': 180, 'reset': 1459422554}
            remaining = data['resources']['statuses']['/statuses/user_timeline']['remaining']
            if remaining < 2:
                break
    except TweepError:
        # even the rate_limit_status method sometime returns 404 or over capacity errors
        pass


def get_tweets_for_all():
    api = get_api()

    count = 20

    screen_names = list(Tweet.objects.values_list('user_screen_name', flat=True).distinct())

    # if we have more than 300 screen_names (or we're above the rate limit for any other reason)
    # then the screen_names at the end of the list wouldn't be updated, this makes that less likely
    random.shuffle(screen_names)

    for screen_name in screen_names:
        try:
            for status in api.user_timeline(screen_name=screen_name, exclude_replies=True, count=count):
                Tweet.save_from_dict(status)
        except TweepError:
            pass

        try:
            data = api.rate_limit_status()  # {'remaining': 178, 'limit': 180, 'reset': 1459422554}
            remaining = data['resources']['statuses']['/statuses/user_timeline']['remaining']
            # print data['resources']['statuses']['/statuses/user_timeline']
            if remaining < 5:
                # this leaves some quota for adding new screen_names, which otherwise won't keep retrying
                break
        except TweepError:
            # the rate_limit_status method sometime returns 404 or over capacity errors
            pass
