from celery.schedules import schedule
from celery.utils.timeutils import remaining, timedelta_seconds, maybe_timedelta
from datetime import timedelta

TWITTER_CONSUMER_KEY = ""
TWITTER_CONSUMER_SECRET = ""
TWITTER_ACCESS_TOKEN = ""
TWITTER_ACCESS_TOKEN_SECRET = ""


CELERYBEAT_CACHE_SHORT_TIME = 60 * 5    # 5 min
CELERYBEAT_CACHE_MED_TIME = 60 * 30   # 30 mins

# The time between each call to to the scheduler.
# Periodic tasks won't be scheduled any more often than this.
CELERYBEAT_MAX_LOOP_INTERVAL = 60  # seconds


class get_tweets_for_all_schedule(schedule):
    def __init__(self, run_every=None, relative=False, nowfun=None):
        self.run_every = timedelta(days=30)  # dummy value, scheduler.is_due overrides it
        self.relative = True
        self.nowfun = nowfun

    def is_due(self, last_run_at):
        # loading dependencies lazily, and caching references on the class:
        if not hasattr(get_tweets_for_all_schedule, "cache"):
            from django.core.cache import cache
            get_tweets_for_all_schedule.cache = cache
        else:
            cache = get_tweets_for_all_schedule.cache
        if not hasattr(get_tweets_for_all_schedule, "Tweet"):
            from .models import Tweet
            get_tweets_for_all_schedule.Tweet = Tweet
        else:
            Tweet = get_tweets_for_all_schedule.Tweet

        # schedule the next time when all timelines will be updated
        num_screen_names = cache.get("num_screen_names")
        if num_screen_names is None:
            num_screen_names = Tweet.objects.values_list('user_screen_name', flat=True).distinct().count()
            cache.set("num_screen_names", num_screen_names, CELERYBEAT_CACHE_SHORT_TIME)

        delay = 60 + (60 * 15 / 300) * num_screen_names
        delay = max(delay, CELERYBEAT_CACHE_SHORT_TIME)  # lower limit is the cache time
        delay = min(delay, 60 * 15) + CELERYBEAT_MAX_LOOP_INTERVAL  # upper limit is 15 minutes (rate limits restart after that)

        remaining_estimate = remaining(last_run_at, maybe_timedelta(delay), relative=self.relative, now=self.now().replace(tzinfo=None))
        remaining_estimate = timedelta_seconds(remaining_estimate)

        # the delay values seem to be ignored here, it calls this method again after CELERYBEAT_MAX_LOOP_INTERVAL anyway
        if remaining_estimate < CELERYBEAT_MAX_LOOP_INTERVAL:
            # print "(True, %s) " % delay
            return (True, delay)  # Run now and ask again later
        else:
            # print "(False, %s) " % remaining_estimate
            return (False, remaining_estimate)  # Don't run now but ask again later


# CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
CELERYBEAT_SCHEDULE = {"get_tweets_for_all": {"task": "twitter.tasks.get_tweets_for_all", "schedule": get_tweets_for_all_schedule()}}
