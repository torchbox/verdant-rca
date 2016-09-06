from datetime import datetime
from time import strptime, mktime
import json

from django.db import models


class Tweet(models.Model):
    tweet_id = models.BigIntegerField(unique=True)
    user_id = models.BigIntegerField()
    user_screen_name = models.CharField(max_length=255)
    created_at = models.DateTimeField()  # 'Tue, 11 Sep 2012 14:02:49 +0000'
    text = models.TextField()
    payload = models.TextField(default='{}')

    @staticmethod
    def parse_date(date_str):
        time_struct = strptime(date_str, "%a %b %d %H:%M:%S +0000 %Y")
        return datetime.fromtimestamp(mktime(time_struct))

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
        tweet.payload = json.dumps(dictionary)
        tweet.save()
        return tweet

    def save(self, *args, **kwargs):
        super(Tweet, self).save(*args, **kwargs)
