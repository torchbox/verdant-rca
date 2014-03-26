from django.utils.text import slugify
from itertools import chain
import re
import json
from wagtail.wagtailcore.models import Page
from modelcluster.fields import ParentalKey
from rca.models import (
    StudentPage, NewStudentPage,

    NewStudentPagePreviousDegree,
    NewStudentPageExhibition,
    NewStudentPageExperience,
    NewStudentPageContactsEmail,
    NewStudentPageContactsPhone,
    NewStudentPageContactsWebsite,
    NewStudentPagePublication,
    NewStudentPageConference,
    NewStudentPageAward,
    NewStudentPageShowCarouselItem,
    NewStudentPageShowCollaborator,
    NewStudentPageShowSponsor,
    NewStudentPageResearchCarouselItem,
    NewStudentPageResearchCollaborator,
    NewStudentPageResearchSponsor,
    NewStudentPageResearchSupervisor,
)


class StudentPageProxy(StudentPage):
    class Meta:
        proxy = True

    @property
    def is_research_page(self):
        return self.degree_qualification in ['mphil', 'phd', 'researchstudent', 'innovationrca-fellow']

    @property
    def is_ma_page(self):
        return self.degree_qualification == 'ma'

    @property
    def is_in_show(self):
        return self.get_parent().id == 5255

    @property
    def is_in_rcanow(self):
        return self.get_parent().id == 36


class StudentMigration(object):
    def __init__(self, save=False, index_page=None, migrate=True, update_references=False):
        self.save = save
        self.skipped_students = []
        self.index_page = Page.objects.get(pk=index_page) if index_page else None
        self.migrate = migrate
        self.update_references = update_references

        # Some regexes for cleaning titles
        self.re_multi_space = re.compile(' +')
        self.re_start_space = re.compile('^ +')
        self.re_end_space = re.compile(' +$')

    def update_page_references(self, old_page, new_page):
        # Get relations
        model = old_page.__class__
        relations = model._meta.get_all_related_objects(include_hidden=True, include_proxy_eq=True)

        # Remove wagtailcore relations
        relations = [relation for relation in relations if not relation.model._meta.app_label == 'wagtailcore']

        # Remove ParentalKey relations
        relations = [relation for relation in relations if not isinstance(relation.field, ParentalKey)]

        # Update references
        for relation in relations:
            # Find objects with references to the old page for this relation
            objects = relation.model._base_manager.filter(
                **{relation.field.name: old_page}
            )

            # If the relation is a page. Look through the revisions table for references
            # We need to check all objects that we know have live objects ('objects') and any pages
            # that have unpublished changes in case a reference was added recently
            if issubclass(relation.model, Page):
                for page in chain(relation.model._base_manager.filter(has_unpublished_changes=True), objects):
                    revision = page.get_latest_revision_as_page()

                    # Make sure the reference is to the old page to avoid mistakes
                    if getattr(revision, relation.field.name) == old_page:
                        setattr(revision, relation.field.name, new_page)

                        if self.save:
                            revision.save_revision()

            # If the foreign key is in a page child. Find the parent pages type and find/update the child object in the revisions table
            try:
                # Note: This only works as all child objects in RCA happen to call their ParentalKey 'page'
                # This will raise an exception if the field doesn't exist
                page_field = relation.model._meta.get_field_by_name('page')[0]

                # Field type must be ParentalKey for this to be a child object
                assert isinstance(page_field, ParentalKey)

                # The parent object must be a page (otherwise there won't be any revisions)
                assert issubclass(page_field.rel.to, Page)
            except:
                pass
            else:
                # Get pages that may contain a reference
                for page in chain(
                        page_field.rel.to._base_manager.filter(has_unpublished_changes=True),
                        [obj.page for obj in objects]
                    ):

                    # Check if there is a revision
                    if page.get_latest_revision():
                        # Get latest revision for this page as JSON
                        revision = json.loads(page.get_latest_revision().content_json)

                        # Find references in the json and change them
                        changed = False
                        if page_field.rel.related_name in revision:
                            for child_object in revision[page_field.rel.related_name]:
                                if relation.field.name in child_object:
                                    if child_object[relation.field.name] == old_page.pk:
                                        changed = True
                                        child_object[relation.field.name] = new_page.pk

                        if changed and self.save:
                            page.revisions.create(content_json=json.dumps(revision))

            # Update objects in the database
            if self.save:
                objects.update(
                    **{relation.field.name: new_page}
                )

    def migrate_page(self, new_page, page):
        # General info
        new_page.first_name = page.first_name
        new_page.last_name = page.last_name
        new_page.profile_image = page.profile_image
        new_page.statement = page.statement
        new_page.twitter_handle = page.student_twitter_feed
        new_page.funding = page.funding
        new_page.feed_image = page.feed_image
        new_page.show_on_homepage = page.show_on_homepage

        # MA info
        if page.is_ma_page:
            new_page.ma_school = page.school
            new_page.ma_programme = page.programme
            new_page.ma_graduation_year = page.graduation_year or page.degree_year
            new_page.ma_specialism = page.specialism
            new_page.ma_in_show = page.is_in_show

        # Research info
        if page.is_research_page:
            new_page.research_school = page.school
            new_page.research_programme = page.programme
            new_page.research_start_year = page.degree_year
            new_page.research_graduation_year = page.graduation_year
            new_page.research_qualification = page.degree_qualification
            #research_dissertation_title
            new_page.research_statement = page.work_description
            new_page.research_work_location = page.work_location
            new_page.research_in_show = page.is_in_show

        # General child objects
        for degree in page.degrees.all():
            new_page.previous_degrees.add(NewStudentPagePreviousDegree(degree=degree.degree))

        for exhibition in page.exhibitions.all():
            new_page.exhibitions.add(NewStudentPageExhibition(exhibition=exhibition.exhibition))

        for experience in page.experiences.all():
            new_page.experiences.add(NewStudentPageExperience(experience=experience.experience))

        for email in page.email.all():
            new_page.emails.add(NewStudentPageContactsEmail(email=email.email))

        for phone in page.phone.all():
            new_page.phones.add(NewStudentPageContactsPhone(phone=phone.phone))

        for website in page.website.all():
            new_page.websites.add(NewStudentPageContactsWebsite(website=website.website))

        for publication in page.publications.all():
            new_page.publications.add(NewStudentPagePublication(name=publication.name))

        for conference in page.conferences.all():
            new_page.conferences.add(NewStudentPageConference(name=conference.name))

        for award in page.awards.all():
            new_page.awards.add(NewStudentPageAward(award=award.award))

        for supervisor in page.supervisors.all():
            new_page.research_supervisors.add(NewStudentPageResearchSupervisor(supervisor=supervisor.supervisor, supervisor_other=supervisor.supervisor_other))

        # Move carousel items/collaborators/sponsors to research if this is a research student
        if page.is_research_page:
            for carousel_item in page.carousel_items.all():
                new_page.research_carousel_items.add(NewStudentPageResearchCarouselItem(
                    image=carousel_item.image,
                    overlay_text=carousel_item.overlay_text,
                    link=carousel_item.link,
                    link_page=carousel_item.link_page,
                    embedly_url=carousel_item.embedly_url,
                    poster_image=carousel_item.poster_image,
                ))

            for collaborator in page.collaborators.all():
                new_page.research_collaborators.add(NewStudentPageResearchCollaborator(name=collaborator.name))

            for sponsor in page.sponsor.all():
                new_page.research_sponsors.add(NewStudentPageResearchSponsor(name=sponsor.name))

        # If this is not a research student, move carousel items/collaborators/sponsors to show
        if not page.is_research_page:
            # Show info
            new_page.show_work_type = page.work_type
            new_page.show_work_location = page.work_location
            new_page.show_work_description = page.work_description

            for carousel_item in page.carousel_items.all():
                new_page.show_carousel_items.add(NewStudentPageShowCarouselItem(
                    image=carousel_item.image,
                    overlay_text=carousel_item.overlay_text,
                    link=carousel_item.link,
                    link_page=carousel_item.link_page,
                    embedly_url=carousel_item.embedly_url,
                    poster_image=carousel_item.poster_image,
                ))

            for collaborator in page.collaborators.all():
                new_page.show_collaborators.add(NewStudentPageShowCollaborator(name=collaborator.name))

            for sponsor in page.sponsor.all():
                new_page.show_sponsors.add(NewStudentPageShowSponsor(name=sponsor.name))

    def migrate_student(self, name, page):
        # Create new page
        new_page = NewStudentPage()
        new_page.title = name
        new_page.slug = slugify(name)
        new_page.live = page.live
        new_page.has_unpublished_changes = not new_page.live

        # Migrate old page
        self.migrate_page(new_page, page)

        # Save new page
        if self.save and self.index_page:
            self.index_page.add_child(new_page)
            new_page.save_revision()

        return new_page

    def clean_student_name(self, name):
        # Some student pages have a suffix, remove the suffix
        bad_suffixes = [', PhD', ', MPhil', ' MA', ' PhD', ' CX PhD Candidate']
        for bad_suffix in bad_suffixes:
            if name.endswith(bad_suffix):
                name = name[:-len(bad_suffix)]

        # Some student pages contain extra spaces
        name = self.re_multi_space.sub(' ', name)
        name = self.re_start_space.sub('', name)
        name = self.re_end_space.sub('', name)

        return name

    def run(self):
        # Get students
        students = {}
        for student in StudentPageProxy.objects.all():
            name = self.clean_student_name(student.title)

            # Put the student page in the students mapping
            if name in students.keys():
                students[name].append(student)
            else:
                students[name] = [student]

        # Migrate each one
        if self.migrate:
            for student, pages in students.items():
                print "Migrating: " + student

                # Skip if this student has multiple pages
                if len(pages) > 1:
                    self.skipped_students.append(student)
                    continue

                # Migrate student
                self.migrate_student(student, pages[0])

        # Update references
        if self.update_references:
            for student, pages in students.items():
                print "Updating references: " + student
                try:
                    new_page = NewStudentPage.objects.get(title=student)

                    for page in pages:
                        self.update_page_references(page, new_page)
                except NewStudentPage.DoesNotExist:
                    print "WARNING: Cannot find new student page for " + student


def run(*args, **kwargs):
    sm = StudentMigration(*args, **kwargs)
    sm.run()

    print repr(sm.skipped_students)
