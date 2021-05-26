import csv

from django.core.management.base import BaseCommand

from rca.models import RcaBlogPage, EventItem, NewsItem, PressRelease


class Command(BaseCommand):
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

        # Blog pages
        with open('blog_pages.csv', 'wb') as f:
            csvf = csv.writer(f)
            csvf.writerow(headers)
            for p in RcaBlogPage.objects.order_by("pk"):
                csvf.writerow([
                    p.title.encode("utf-8"),
                    p.date,
                    p.latest_revision_created_at.strftime("%Y-%m-%d") if p.latest_revision_created_at else "",
                    p.owner,
                    p.author,
                    "",
                    '|'.join([t.name for t in p.tags.all()]),
                    p.url
                ])
        
        # Event pages
        with open('event_pages.csv', 'wb') as f:
            csvf = csv.writer(f)
            csvf.writerow(headers)
            for p in EventItem.objects.order_by("pk"):
                csvf.writerow([
                    p.title.encode("utf-8"),
                    p.first_published_at.strftime("%Y-%m-%d") if p.first_published_at else "",
                    p.latest_revision_created_at.strftime("%Y-%m-%d") if p.latest_revision_created_at else "",
                    p.owner,
                    "",
                    "",
                    '|'.join([t.name for t in p.tags.all()]),
                    p.url
                ])
        
        with open('news_pages.csv', 'wb') as f:
            csvf = csv.writer(f)
            csvf.writerow(headers)
            for p in NewsItem.objects.order_by("pk"):
                csvf.writerow([
                    p.title.encode("utf-8"),
                    p.date,
                    p.latest_revision_created_at.strftime("%Y-%m-%d") if p.latest_revision_created_at else "",
                    p.owner,
                    p.author,
                    p.intro.encode("utf-8"),
                    '|'.join([t.name for t in p.tags.all()]),
                    p.url
                ])
        
        with open('press_release_pages.csv', 'wb') as f:
            csvf = csv.writer(f)
            csvf.writerow(headers)
            for p in PressRelease.objects.order_by("pk"):
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
