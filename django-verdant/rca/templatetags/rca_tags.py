from django import template

from rca.models import EventItem
from datetime import date

register = template.Library()

@register.inclusion_tag('rca/includes/modules/upcoming_events.html')
def upcoming_events(count=3):
    events = EventItem.objects.filter(date_from__gte=date.today()).order_by('date_from')[:count]
    return {
        'events': events
    }
