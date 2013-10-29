/*
// http://tweet.seaofclouds.com/

$("#tweets").tweet({
  join_text: "auto",
  username: "Torchbox",
  avatar_size: 32,
  auto_join_text_default: "Torchbox said",
  loading_text: "Checking for new tweets...",
  count: 1
});

*/



!function(factory) {
    if (typeof define === "function" && define.amd) define(["jquery"], factory);
    else factory(jQuery)
}(function($) {
    $.fn.tweet = function(o) {
        var s = $.extend({
            username: null,
            list: null,
            favorites: false,
            query: null,
            avatar_size: null,
            count: 3,
            fetch: null,
            page: 1,
            retweets: true,
            intro_text: null,
            outro_text: null,
            join_text: null,
            loading_text: null,
            refresh_interval: null,
            twitter_url: "twitter.com",
            twitter_api_url: window.location.host + "/twitter",
            twitter_search_url: "search.twitter.com",
            template: "{avatar}{time}{join} {text}",
            comparator: function(tweet1, tweet2) {
                return tweet2.tweet_time - tweet1.tweet_time
            },
            filter: function(tweet) {
                return true
            }
        }, o);
        s.auto_join_text_url = s.auto_join_text_url || s.auto_join_text_default;
        var url_regexp = /\b((?:https?:\/\/|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}\/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))/gi;

        function t(template, info) {
            if (typeof template === "string") {
                var result = template;
                for (var key in info) {
                    var val = info[key];
                    result = result.split("{" + key + "}").join(val === null ? "" : val)
                }
                return result
            } else return template(info)
        }
        $.extend({
            tweet: {
                t: t
            }
        });

        function replacer(regex, replacement) {
            return function() {
                var returning = [];
                this.each(function() {
                    returning.push(this.replace(regex, replacement))
                });
                return $(returning)
            }
        }
        function escapeHTML(s) {
            return s.replace(/</g, "&lt;").replace(/>/g, "^&gt;")
        }
        $.fn.extend({
            linkUser: replacer(/(^|[\W])@(\w+)/gi, '$1<span class="at">@</span><a href="http://' + s.twitter_url + '/$2">$2</a>'),
            linkHash: replacer(/(?:^| )[\#]+([\w\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u00ff\u0600-\u06ff]+)/gi, ' <a href="https://twitter.com/search?q=%23$1&lang=all' + (s.username && s.username.length === 1 && !s.list ? "&from=" + s.username.join("%2BOR%2B") : "") + '" class="tweet_hashtag">#$1</a>'),
            makeHeart: replacer(/(&lt;)+[3]/gi, "<tt class='heart'>&#x2665;</tt>")
        });

        function linkURLs(text, entities) {
            return text.replace(url_regexp, function(match) {
                var url = /^[a-z]+:/i.test(match) ? match : "http://" + match;
                var text = match;
                for (var i = 0; i < entities.length; ++i) {
                    var entity = entities[i];
                    if (entity.url === url && entity.expanded_url) {
                        url = entity.expanded_url;
                        text = entity.display_url;
                        break
                    }
                }
                return '<a href="' + escapeHTML(url) + '">' + escapeHTML(text) + "</a>"
            })
        }
        function parse_date(date_str) {
            return Date.parse(date_str.replace(/^([a-z]{3})( [a-z]{3} \d\d?)(.*)( \d{4})$/i, "$1,$2$4$3"))
        }
        function extract_relative_time(date) {
            var toInt = function(val) {
                    return Math.round(parseFloat(val))
                };
            var relative_to = new Date;
            var delta = toInt((relative_to.getTime() - date) / 1e3);
            if (delta < 1) delta = 0;
            return {
                days: toInt(delta / 86400),
                hours: toInt(delta / 3600),
                minutes: toInt(delta / 60),
                seconds: toInt(delta)
            }
        }
        function format_relative_time(time_ago) {
            if (time_ago.days > 2) return "about " + time_ago.days + " days ago";
            if (time_ago.hours > 24) return "about a day ago";
            if (time_ago.hours > 2) return "about " + time_ago.hours + " hours ago";
            if (time_ago.minutes > 45) return "about an hour ago";
            if (time_ago.minutes > 2) return "about " + time_ago.minutes + " minutes ago";
            if (time_ago.seconds > 1) return "about " + time_ago.seconds + " seconds ago";
            return "just now"
        }
        function build_auto_join_text(text) {
            if (text.match(/^(@([A-Za-z0-9-_]+)) .*/i)) {
                return s.auto_join_text_reply
            } else if (text.match(url_regexp)) {
                return s.auto_join_text_url
            } else if (text.match(/^((\w+ed)|just) .*/im)) {
                return s.auto_join_text_ed
            } else if (text.match(/^(\w*ing) .*/i)) {
                return s.auto_join_text_ing
            } else {
                return s.auto_join_text_default
            }
        }
        function build_api_url() {
            var proto = "https:" === document.location.protocol ? "https:" : "http:";
            var count = s.fetch === null ? s.count : s.fetch;
            var common_params = "&include_entities=1&callback=?";
            if (s.list) {
                return proto + "//" + s.twitter_api_url + "/1/" + s.username[0] + "/lists/" + s.list + "/statuses.json?page=" + s.page + "&per_page=" + count + common_params
            } else if (s.favorites) {
                return proto + "//" + s.twitter_api_url + "/1/favorites.json?screen_name=" + s.username[0] + "&page=" + s.page + "&count=" + count + common_params
            } else if (s.query === null && s.username.length === 1) {
                return proto + "//" + s.twitter_api_url + "/1/statuses/user_timeline.json?screen_name=" + s.username[0] + "&count=" + count + (s.retweets ? "&include_rts=1" : "") + "&page=" + s.page + common_params
            } else {
                var query = s.query || "from:" + s.username.join(" OR from:");
                return proto + "//" + s.twitter_search_url + "/search.json?&q=" + encodeURIComponent(query) + "&rpp=" + count + "&page=" + s.page + common_params
            }
        }
        function extract_avatar_url(item, secure) {
            if (secure) {
                return "user" in item ? item.user.profile_image_url_https : extract_avatar_url(item, false).replace(/^http:\/\/[a-z0-9]{1,3}\.twimg\.com\//, "https://s3.amazonaws.com/twitter_production/")
            } else {
                return item.profile_image_url || item.user.profile_image_url
            }
        }
        function extract_template_data(item) {
            var o = {};
            o.item = item;
            o.source = item.source;
            o.screen_name = item.from_user || item.user.screen_name;
            o.name = item.from_user_name || item.user.name;
            o.retweet = typeof item.retweeted_status != "undefined";
            o.tweet_time = parse_date(item.created_at);
            o.join_text = s.join_text === "auto" ? build_auto_join_text(item.text) : s.join_text;
            o.tweet_id = item.id_str;
            o.twitter_base = "http://" + s.twitter_url + "/";
            o.user_url = o.twitter_base + o.screen_name;
            o.tweet_url = o.user_url + "/status/" + o.tweet_id;
            o.reply_url = o.twitter_base + "intent/tweet?in_reply_to=" + o.tweet_id;
            o.retweet_url = o.twitter_base + "intent/retweet?tweet_id=" + o.tweet_id;
            o.favorite_url = o.twitter_base + "intent/favorite?tweet_id=" + o.tweet_id;
            o.retweeted_screen_name = o.retweet && item.retweeted_status.user.screen_name;
            o.tweet_relative_time = format_relative_time(extract_relative_time(o.tweet_time));
            o.entities = item.entities ? (item.entities.urls || []).concat(item.entities.media || []) : [];
            o.tweet_raw_text = o.retweet ? "RT @" + o.retweeted_screen_name + " " + item.retweeted_status.text : item.text;
            o.tweet_text = $([linkURLs(o.tweet_raw_text, o.entities)]).linkUser().linkHash()[0];
            o.retweeted_tweet_text = $([linkURLs(item.text, o.entities)]).linkUser().linkHash()[0];
            o.tweet_text_fancy = $([o.tweet_text]).makeHeart()[0];
            o.avatar_size = s.avatar_size;
            o.avatar_url = extract_avatar_url(o.retweet ? item.retweeted_status : item, document.location.protocol === "https:");
            o.avatar_screen_name = o.retweet ? o.retweeted_screen_name : o.screen_name;
            o.avatar_profile_url = o.twitter_base + o.avatar_screen_name;
            o.user = t('<a class="tweet-user" href="{user_url}">{screen_name}</a>', o);
            o.join = s.join_text ? t('<span class="tweet-join"> {join_text}</span>', o) : "";
            o.avatar = o.avatar_size ? t('<a class="tweet-avatar" href="{avatar_profile_url}"><img src="{avatar_url}" height="{avatar_size}" width="{avatar_size}" alt="{avatar_screen_name}\'s avatar" title="{avatar_screen_name}\'s avatar" border="0"/></a>', o) : "";
            o.time = t('<span class="tweet-time"><a href="{tweet_url}" title="View tweet on twitter">{tweet_relative_time}</a></span>', o);
            o.text = t('<span class="tweet-text">{tweet_text_fancy}</span>', o);
            o.retweeted_text = t('<span class="tweet-text">{retweeted_tweet_text}</span>', o);
            o.reply_action = t('<a class="tweet-action tweet-reply" href="{reply_url}">reply</a>', o);
            o.retweet_action = t('<a class="tweet-action tweet-retweet" href="{retweet_url}">retweet</a>', o);
            o.favorite_action = t('<a class="tweet-action tweet-favorite" href="{favorite_url}">favorite</a>', o);
            return o
        }
        function render_tweets(widget, tweets) {
            var list = $('<ul class="tweet-list">');
            list.append($.map(tweets, function(o) {
                return "<li>" + t(s.template, o) + "</li>"
            }).join("")).children("li:first").addClass("tweet-first").end().children("li:odd").addClass("tweet-even").end().children("li:even").addClass("tweet-odd");
            $(widget).empty().append(list);
            if (s.intro_text) list.before('<p class="tweet-intro">' + s.intro_text + "</p>");
            if (s.outro_text) list.after('<p class="tweet-outro">' + s.outro_text + "</p>");
            $(widget).trigger("loaded").trigger(tweets.length === 0 ? "empty" : "full");
            if (s.refresh_interval) {
                window.setTimeout(function() {
                    $(widget).trigger("tweet:load")
                }, 1e3 * s.refresh_interval)
            }
        }
        function load(widget) {
            var loading = $('<p class="loading">' + s.loading_text + "</p>");
            if (s.loading_text) $(widget).not(":has(.tweet_list)").empty().append(loading);
            $.getJSON(build_api_url(), function(data) {
                var tweets = $.map(data.results || data, extract_template_data);
                tweets = $.grep(tweets, s.filter).sort(s.comparator).slice(0, s.count);
                $(widget).trigger("tweet:retrieved", [tweets])
            })
        }
        return this.each(function(i, widget) {
            if (s.username && typeof s.username === "string") {
                s.username = [s.username]
            }
            $(widget).unbind("tweet:render").unbind("tweet:retrieved").unbind("tweet:load").bind({
                "tweet:load": function() {
                    load(widget)
                },
                "tweet:retrieved": function(ev, tweets) {
                    $(widget).trigger("tweet:render", [tweets])
                },
                "tweet:render": function(ev, tweets) {
                    render_tweets($(widget), tweets)
                }
            }).trigger("tweet:load")
        })
    }
});

