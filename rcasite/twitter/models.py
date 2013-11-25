from datetime import datetime
from time import strptime, mktime

import simplejson

from django.db import models

from .fields import JSONField


class Tweet(models.Model):
    """
    Model for storing tweets retrieved by a periodic task.
    Given the rate limiting for the single app authentication
    this is a more reliable way storing tweets than with memcache only.
    And also allows for features like moderation in the future.
    """

    tweet_id = models.BigIntegerField(unique=True)
    user_id = models.BigIntegerField()
    user_screen_name = models.CharField(max_length=255)
    created_at = models.DateTimeField()  # 'Tue, 11 Sep 2012 14:02:49 +0000'
    text = models.TextField()
    payload = JSONField()

    @staticmethod
    def parse_date(date_str):
        time_struct = strptime(date_str, "%a %b %d %H:%M:%S +0000 %Y")
        return datetime.fromtimestamp(mktime(time_struct))

    @staticmethod
    def save_from_json(json):
        return Tweet.save_from_dict(simplejson.loads(json))

    @staticmethod
    def save_from_dict(dictionary):
        try:
            tweet = Tweet.objects.get(tweet_id=int(dictionary["id"]))
        except Tweet.DoesNotExist:
            tweet = Tweet(tweet_id=int(dictionary["id"]))

        tweet.created_at = Tweet.parse_date(dictionary["created_at"])
        tweet.user_id = int(dictionary["user"]["id"])
        tweet.user_screen_name = dictionary["user"]["screen_name"]
        tweet.text = dictionary["text"]
        tweet.payload = simplejson.dumps(dictionary)
        tweet.save()
        return tweet

    def save(self, *args, **kwargs):
        super(Tweet, self).save(*args, **kwargs)
