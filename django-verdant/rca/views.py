from django.shortcuts import render
from django.db.models import Min

from rca.models import EventItem

"""
Views defined here are global ones that live at a fixed URL (defined in rca/app_urls.py)
unrelated to the site tree structure. Typically this would be used for things like content
pulled in via AJAX.
"""

def events(request):
    programme = request.GET.get('programme')

    events = EventItem.future_objects.annotate(start_date=Min('dates_times__date_from')).order_by('start_date')
    if programme:
        events = events.filter(related_programmes__programme=programme)

    return render(request, "rca/tags/upcoming_events.html", {
        'events': events,
    })
