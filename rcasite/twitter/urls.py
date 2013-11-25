from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^1/statuses/user_timeline.json$',
        "twitter.views.statuses_user_timeline",
        name="twitter_1_statuses_user_timeline"
    ),
)
