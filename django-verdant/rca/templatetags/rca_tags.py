from django import template

from rca.models import EventItem
from datetime import date

register = template.Library()

@register.inclusion_tag('rca/includes/modules/upcoming_events.html', takes_context=True)
def upcoming_events(context, count=3):
    events = EventItem.objects.filter(date_to__gte=date.today()).order_by('date_from')[:count]
    return {
        'events': events,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/includes/modules/carousel-news.html', takes_context=True)
def news_carousel(context, count=6):
    news_items = NewsItem.objects.filter(area=self.news_carousel_area)[:count]
    return {
        'news_items': news_items,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }
