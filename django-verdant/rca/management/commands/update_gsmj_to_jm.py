import datetime

from django.core.management.base import NoArgsCommand
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, models, transaction

from rca.models import *

help = """

This will updated the following pages by replacing
'goldsmithingsilversmithingmetalworkjewellery' with 'jewelleryandmetal':

The page types below should be changed based on the date in the 'year' field:

ResearchItem + year
AlumniPage + year
InnovationRCAProject + year
ReachOutRCAProject + year

The page types below should be changed based on their last published date (after Oct 1st 2014):

StandardPage.related_programme
JobPage
StaffPageRole
RcaNowPage
RcaBlogPage
NewsItemRelatedProgramme
PressReleaseRelatedProgramme
EventItemRelatedProgramme

Press y to continue

"""


def update_page(page, programme_field):
    if programme_field == 'programme':
        page.programme = 'jewelleryandmetal'
    if programme_field == 'related_programme':
        page.programme = 'jewelleryandmetal'

    if page.has_unpublished_changes:
        # modify the live page directly
        page.save()

        # update latest draft revision too
        revision = page.get_latest_revision()
        revision_data = json.loads(revision.content_json)

        if revision_data[programme_field] == 'goldsmithingsilversmithingmetalworkjewellery':
            revision_data[programme_field] = 'jewelleryandmetal'

        revision.content_json = json.dumps(revision_data, cls=DjangoJSONEncoder)
        revision.save()
    else:
        # if there aren't any drafts then just publish a new revision normally
        page.save_revision().publish()


def update_related(page, related_field):
    if page.has_unpublished_changes:

        # modify the live page directly
        if related_field == 'roles':
            page.roles.filter(programme='goldsmithingsilversmithingmetalworkjewellery').update(programm='jewelleryandmetal')
        if related_field == 'related_programmes':
            page.related_programmes.filter(programme='goldsmithingsilversmithingmetalworkjewellery').update(programm='jewelleryandmetal')

        # update latest draft revision too
        revision = page.get_latest_revision()
        revision_data = json.loads(revision.content_json)

        for related in revision_data[related_field]:
            if related['programme'] == 'goldsmithingsilversmithingmetalworkjewellery':
                related['programme'] = 'jewelleryandmetal'

        revision.content_json = json.dumps(revision_data, cls=DjangoJSONEncoder)
        revision.save()
    else:
        # if there aren't any drafts then just publish a new revision normally
        revision = page.save_revision()
        revision_data = json.loads(revision.content_json)

        for related in revision_data[related_field]:
            if related['programme'] == 'goldsmithingsilversmithingmetalworkjewellery':
                related['programme'] = 'jewelleryandmetal'

        revision.content_json = json.dumps(revision_data, cls=DjangoJSONEncoder)
        revision.save()
        revision.publish()


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        if not "y" == raw_input(help).lower():
            return
        count = 0

        commit = True

        # The page types below should be changed based on the date in the 'year' field:
        for ptype in [ResearchItem, AlumniPage, InnovationRCAProject, ReachOutRCAProject]:
            for page in ptype.objects.filter(
                live=True,
                year__gte=2014,
                programme='goldsmithingsilversmithingmetalworkjewellery',
            ):
                print page.id
                count += 1
                if commit:
                    update_page(page, 'programme')

        # The page types below should be changed based on their last published date (after Oct 1st 2014):
        for page in StandardPage.objects.filter(
            live=True,
            latest_revision_created_at__gte=datetime.date(2014, 10, 1),
            related_programme='goldsmithingsilversmithingmetalworkjewellery',
        ):
            print page.id
            count += 1
            if commit:
                update_page(page, 'related_programme')

        for ptype in [JobPage, RcaNowPage, RcaBlogPage]:
            for page in ptype.objects.filter(
                live=True,
                latest_revision_created_at__gte=datetime.date(2014, 10, 1),
                programme='goldsmithingsilversmithingmetalworkjewellery',
            ):
                print page.id
                count += 1
                if commit:
                    update_page(page, 'programme')

        for page in StaffPage.objects.filter(
            live=True,
            latest_revision_created_at__gte=datetime.date(2014, 10, 1),
            roles__programme='goldsmithingsilversmithingmetalworkjewellery',
        ):
            print page.id
            count += 1
            if commit:
                update_related(page, 'roles')

        # NewsItemRelatedProgramme          NewsItem       .related_programmes
        # PressReleaseRelatedProgramme      PressRelease   .related_programmes
        # EventItemRelatedProgramme         EventItem      .related_programmes
        for ptype in [NewsItem, PressRelease, EventItem]:
            for page in ptype.objects.filter(
                live=True,
                latest_revision_created_at__gte=datetime.date(2014, 10, 1),
                related_programmes__programme='goldsmithingsilversmithingmetalworkjewellery',
            ):
                print page.id
                count += 1
                if commit:
                    update_related(page, 'related_programmes')

        print "Number of pages modified:"
        print count
