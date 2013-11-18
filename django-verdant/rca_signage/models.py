from django.http import HttpResponse, Http404
from django.db.models import Q
from django.shortcuts import render
from core.models import Page
from rca.models import EventItem, EventItemDatesTimes
from constants import SCREEN_CHOICES, SCREEN_CHOICES_DICT
import datetime


class ScreenIndex(Page):
    indexed = False

    def route(self, request, path_components):
        # If this page is not published, raise 404 error
        if not self.live:
            raise Http404

        if path_components:
            # Request is for a screen
            return self.serve(request, screen=path_components[0], extra_path='/'.join(path_components[1:]))
        else:
            # Request is for screens index
            return self.serve(request)

    def serve_screen(self, request, screen, extra_path=None):
        # Check for special event
        special_events = EventItemDatesTimes.objects.filter(page__screens__screen=screen, page__special_event=True, page__live=True)
        if len(special_events) > 0:
            return render(request, 'rca_signage/special_event.html', {
                'screen': dict(slug=screen, name=SCREEN_CHOICES_DICT[screen]),
                'date': datetime.date(2013, 9, 28),
                'event': special_events[0],
            })
        else:
            # Start and end dates
            start_date = datetime.date(2013, 9, 28)
            end_date = start_date + datetime.timedelta(days=70)
            day_count = (end_date - start_date).days + 1

            # Get list of dates
            dates = [
                start_date + datetime.timedelta(days=day_num)
                for day_num in range(day_count)
            ]

            # Add a list of events to each day
            days = [{
                'date': date,
                'events': EventItemDatesTimes.objects.filter(page__live=True).filter(
                    Q(date_from__lte=date, date_to__gte=date) | # Multi day events
                    Q(date_from=date, date_to=None) # Single day events
                )
            } for date in dates]

            # Remove days without any events
            days = filter(lambda day: len(day['events']) > 0, days)

            return render(request, 'rca_signage/upcoming_events.html', {
                'screen': dict(slug=screen, name=SCREEN_CHOICES_DICT[screen]),
                'days': days,
            })

        return HttpResponse("This is the screen page '%s' (%s)" % (screen, extra_path))

    def serve(self, request, screen=None, extra_path=None):
        # Check if this request is for a screen
        if screen:
            # Check that screen exists
            if not screen in SCREEN_CHOICES_DICT:
                raise Http404("Screen doesn't exist")

            return self.serve_screen(request, screen, extra_path=extra_path)
        else:
            return render(request, 'rca_signage/index.html', {
                'screens': [dict(slug=screen[0], name=screen[1]) for screen in SCREEN_CHOICES],
            })