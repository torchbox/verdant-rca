from django.http import HttpResponse, Http404
from django.db.models import Q
from django.shortcuts import render
from django.template.loader import render_to_string
from core.models import Page
from rca.models import EventItemDatesTimes, EventItem
from constants import SCREEN_CHOICES, SCREEN_CHOICES_DICT
import datetime
import json


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

    def get_upcoming_events(self, start_date=None, max_days=28, max_events=10):
        # Get start date
        if start_date is None:
            start_date = datetime.date.today()
        events = []

        for day_num in range(max_days):
            # Work out date
            date = start_date + datetime.timedelta(days=day_num)

            # Get event dates times for this day
            event_dates_times = EventItemDatesTimes.objects.filter(page__live=True).filter(
                Q(date_from__lte=date, date_to__gte=date) | # Multi day events
                Q(date_from=date, date_to=None) # Single day events
            )

            # Add all events for this day to events list
            for event_date_time in event_dates_times:
                events.append((date, event_date_time))
                if len(events) >= max_events:
                    return events

        return events

    def get_slides(self, screen):
        slides = []

        # Check for special event
        special_events = EventItemDatesTimes.objects.filter(page__screens__screen=screen, page__special_event=True, page__live=True)
        if len(special_events) > 0:
            for event in special_events:
                slides.append(('rca_signage/special_event_slide.html', {
                    'event': event,
                }))

            return slides

        # No special event, get upcoming events instead

        # Get list of upcoming events
        upcoming_events = self.get_upcoming_events()

        # Build slides
        def build_upcoming_events_slide(events):
            # Return if there are no events
            if len(events) == 0:
                return None

            # Sort events into days
            days = []
            previous_date = None
            for event in events:
                # If date changed, create new day
                if event[0] != previous_date:
                    previous_date = event[0]
                    days.append({
                        'date': event[0],
                        'events': [],
                    })

                # Add event to current day
                days[-1]['events'].append(event[1])

            # Return new slide
            return ('rca_signage/upcoming_events_slide.html', dict(days=days))

        first_slide = build_upcoming_events_slide(upcoming_events[:5])
        if not first_slide is None:
            slides.append(first_slide)
        else:
            slides.append(('rca_signage/upcoming_events_slide.html', dict(days=[])))

        second_slide = build_upcoming_events_slide(upcoming_events[5:])
        if not second_slide is None:
            slides.append(second_slide)

        return slides

    def serve_slides(self, request, screen):
        # Get slides
        slides = []
        for slide in self.get_slides(screen):
            context = {
                'screen': dict(slug=screen, name=SCREEN_CHOICES_DICT[screen]),
                'date': datetime.date.today(),
            }
            context.update(slide[1])
            slides.append(render_to_string(slide[0], context))

        # Return as JSON
        return HttpResponse(json.dumps(slides))

    def serve_screen(self, request, screen, extra_path=None):
        if extra_path == 'slides':
            return self.serve_slides(request, screen)

        return render(request, 'rca_signage/screen.html', {
                'screen': dict(slug=screen, name=SCREEN_CHOICES_DICT[screen]),
            })

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