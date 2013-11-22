from datetime import timedelta
import random

import tweepy
from celery.decorators import task
from celery.task import PeriodicTask

from django.conf import settings

from .models import Tweet


def _get_api():
    # app level rate limit: 300 request every 15 minutes
    auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
    auth.set_access_token(settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())
    return api


@task
def get_tweets_async(screen_name="RCAevents", count=10):
    api = _get_api()

    count = count if count < 50 else 50

    if api.get_user(screen_name=screen_name)["protected"]:
        return

    for status in api.user_timeline(screen_name=screen_name, exclude_replies=True, count=count):
        Tweet.save_from_dict(status)
        if int(dict(api.last_response.getheaders())["x-rate-limit-remaining"]) < 1:
            break


def get_tweets(screen_name="RCAevents", count=10):
    api = _get_api()

    count = count if count < 50 else 50

    if api.get_user(screen_name=screen_name)["protected"]:
        return

    for status in api.user_timeline(screen_name=screen_name, exclude_replies=True, count=count):
        Tweet.save_from_dict(status)
        if int(dict(api.last_response.getheaders())["x-rate-limit-remaining"]) < 1:
            break


class get_tweets_for_all(PeriodicTask):

    run_every = timedelta(days=30)  # dummy value, scheduler.is_due overrides it

    def run(self):
        api = _get_api()

        count = 20

        screen_names = list(Tweet.objects.values_list('user_screen_name', flat=True).distinct())

        # if we have more than 300 screen_names (or we're above the rate limit for any other reason)
        # then the screen_names at the end of the list wouldn't be updated, this makes that less likely
        random.shuffle(screen_names)

        for screen_name in screen_names:
            for status in api.user_timeline(screen_name=screen_name, exclude_replies=True, count=count):
                Tweet.save_from_dict(status)

            remaining = dict(api.last_response.getheaders()).get("x-rate-limit-remaining")
            if remaining is not None and int(remaining) < 1:
                break


@task
def test_error_email():
    raise Exception("test")
