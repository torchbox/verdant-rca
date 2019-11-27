import csv
import logging
import sys
import warnings
from datetime import date
from optparse import make_option

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from wagtail.wagtailredirects.models import Redirect

from rca.models import EventIndex, EventItem

# Ignore all the deprecation warnings.
# Legacy site, soon to be replaced.
warnings.simplefilter("ignore")


class Command(BaseCommand):
    event_redirects = {}

    option_list = BaseCommand.option_list + (
        make_option(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help="Dry run, do not unpublish pages or create redirects."
        ),
        make_option(
            '--verbose',
            action='store_true',
            dest='verbose',
            default=True,
            help="Provide extended feedback."
        ),
        make_option(
            '--examples',
            action='store_true',
            dest='examples',
            default=False,
            help="Provide urls for example event content."
        ),
        make_option(
            '--csv',
            action='store_true',
            dest='output_csv',
            default=False,
            help="List archived event items. Negates verbose."
        ),
        make_option(
            '--csv-headers',
            action='store_true',
            dest='csv_headers',
            default=True,
            help="Allows false value for additions to file."
        ),
        make_option(
            '--permanent',
            action='store_true',
            dest='permanent',
            default=True,
            help="Create permanent redirects (301)."
        ),
        make_option(
            '--limit',
            dest='limit',
            default=None,
            help="Limit to archiving set number of events."
        ),
    )

    def create_redirect(self, e, target_page, permanent=True):
        new_redirect = Redirect()
        new_redirect.site = e.get_site()
        # Need to remove trailing slash or redirect does not work
        new_redirect.old_path = e.get_url_parts()[2][:-1]
        new_redirect.is_permanent = permanent
        new_redirect.redirect_page = target_page
        new_redirect.save()
        self.event_redirects[e.pk] = new_redirect.id

    def get_csv_rows(self, events, add_headers=False):
        rows = []
        headers = [
            'Event id',
            'Event title',
            'Event URL',
            'Dates from',
            'Dates to',
            'Redirect',
        ]

        if add_headers:
            rows.append(headers)

        for e in events:
            row = []
            row.append(e.pk)
            row.append(e.title)
            row.append(e.url)
            dates = e.dates_times.order_by('date_from').values_list('date_from', 'date_to')
            date_from = []
            for d in dates:
                try:
                    date_from.append(d[0].strftime("%d/%m/%Y"))
                except Exception:
                    date_from = ''

            date_to = []
            for d in dates:
                try:
                    date_to.append(d[1].strftime("%d/%m/%Y"))
                except Exception:
                    date_to = ''

            row.append('|'.join(date_from))
            row.append('|'.join(date_to))
            if self.event_redirects:
                row.append('{}admin/redirects/{}/'.format(
                    e.get_site().root_url,
                    self.event_redirects[e.pk])
                )
            else:
                row.append('')
            rows.append(row)

        return rows

    def handle(self, **options):
        # Disable logging as a workaround for character encoding bug
        # that causes an error when certain pages are published/unpublished
        logging.disable(logging.CRITICAL)

        verbose = options['verbose']
        examples = options['examples']
        output_csv = options['output_csv']
        csv_headers = options['csv_headers']
        permanent = options['permanent']
        dry_run = options['dry_run']
        limit = options['limit']

        event_index = EventIndex.objects.first()

        if output_csv:
            verbose = False
            examples = False

        events = EventItem.objects.live()
        events_count = events.count()
        two_years_ago = date.today() - relativedelta(years=2)
        events = events.exclude(
            Q(dates_times__date_to__gt=two_years_ago) |
            Q(dates_times__date_from__gt=two_years_ago)
        )

        if limit:
            events = events[:limit]
            if verbose:
                msg = 'Archiving only first {} events.'
                self.stdout.write(
                    msg.format(str(limit))
                )

        if not dry_run:
            with transaction.atomic():
                for event in events:
                    event.unpublish()
                    self.create_redirect(event, event_index, permanent)

        if verbose:
            msg = '{} of {} published events selected for archiving.'
            self.stdout.write(
                msg.format(str(len(events)), str(events_count))
            )

        if examples:
            self.stdout.write('')
            self.stdout.write('Examples:')
            random_events = events.order_by("?")[:4]
            msg = '{} | {}/admin/pages/{}/edit/'
            for e in random_events:
                self.stdout.write(
                    msg.format(e.url, e.get_site().root_url, str(e.pk))
                )

        if output_csv:
            rows = self.get_csv_rows(events, add_headers=csv_headers)
            writer = csv.writer(sys.stdout)
            for row in rows:
                row = [s.encode("utf-8") if hasattr(s, "encode") else s for s in row]
                writer.writerow(row)

        # Re-enable logging
        logging.disable(logging.NOTSET)
