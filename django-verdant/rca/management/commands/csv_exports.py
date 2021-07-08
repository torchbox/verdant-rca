import csv

from django.core.management.base import BaseCommand

from rca.models import EventItem, NewsItem, PressRelease, RcaBlogPage


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "-l",
            "--limit",
            type=int,
            default=None,
            help="Number of days notice being given.",
        )


    def handle(self, **options):
        headers = [
            'Title',
            'Publish Date',
            'Last Edit Date',
            'Creator',
            'Author',
            'Intro',
            'Tags',
            'URL'
        ]

        self.limit = options.get('limit', None)

        # Blog pages
        with open('blog_pages.csv', 'wb') as f:
            csvf = csv.writer(f)
            csvf.writerow(headers)
            pages = RcaBlogPage.objects.order_by("pk")
            if self.limit:
                pages = pages[:self.limit]
            for p in pages:
                csvf.writerow(
                    [
                        p.title.encode("utf-8"),
                        p.date,
                        p.latest_revision_created_at.strftime("%Y-%m-%d")
                        if p.latest_revision_created_at
                        else "",
                        p.owner,
                        p.author,
                        "",
                        '|'.join(t.name for t in p.tags.all()),
                        # self.get_page_url(p),
                        p.url
                    ]
                )


        # Event pages
        with open('event_pages.csv', 'wb') as f:
            csvf = csv.writer(f)
            csvf.writerow(headers)
            pages = EventItem.objects.order_by("pk")
            if self.limit:
                pages = pages[:self.limit]
            for p in pages:
                csvf.writerow(
                    [
                        p.title.encode("utf-8"),
                        p.first_published_at.strftime("%Y-%m-%d")
                        if p.first_published_at
                        else "",
                        p.latest_revision_created_at.strftime("%Y-%m-%d")
                        if p.latest_revision_created_at
                        else "",
                        p.owner,
                        "",
                        "",
                        '|'.join(t.name for t in p.tags.all()),
                        p.url,
                    ]
                )


        with open('news_pages.csv', 'wb') as f:
            csvf = csv.writer(f)
            csvf.writerow(headers)
            pages = NewsItem.objects.order_by("pk")
            if self.limit:
                pages = pages[:self.limit]
            for p in pages:
                csvf.writerow(
                    [
                        p.title.encode("utf-8"),
                        p.date,
                        p.latest_revision_created_at.strftime("%Y-%m-%d")
                        if p.latest_revision_created_at
                        else "",
                        p.owner,
                        p.author,
                        p.intro.encode("utf-8"),
                        '|'.join(t.name for t in p.tags.all()),
                        p.url,
                    ]
                )


        with open('press_release_pages.csv', 'wb') as f:
            csvf = csv.writer(f)
            csvf.writerow(headers)
            pages = PressRelease.objects.order_by("pk")
            if self.limit:
                pages = pages[:self.limit]
            for p in pages:
                csvf.writerow([
                    p.title.encode("utf-8"),
                    p.date,
                    p.latest_revision_created_at.strftime("%Y-%m-%d") if p.latest_revision_created_at else "",
                    p.owner,
                    p.author,
                    p.intro.encode("utf-8"),
                    "",
                    p.url
                ])
