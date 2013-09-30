from django import template

from rca.models import EventItem, NewsItem
from datetime import date

register = template.Library()

# FIXME: order by should really be on the first dates_times object
@register.inclusion_tag('rca/includes/modules/upcoming_events.html', takes_context=True)
def upcoming_events(context, count=3):
    events = EventItem.objects.filter(dates_times__date_to__gte=date.today()).distinct().order_by('dates_times__date_from')[:count]
    return {
        'events': events,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/includes/modules/carousel-news.html', takes_context=True)
def news_carousel(context, area, count=6):
    news_items = NewsItem.objects.filter(area=area)[:count]
    return {
        'news_items': news_items,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }
