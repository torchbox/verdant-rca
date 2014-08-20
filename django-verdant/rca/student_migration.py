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
    NewStudentPageMPhilCarouselItem,
    NewStudentPageMPhilCollaborator,
    NewStudentPageMPhilSponsor,
    NewStudentPageMPhilSupervisor,
    NewStudentPagePhDCarouselItem,
    NewStudentPagePhDCollaborator,
    NewStudentPagePhDSponsor,
    NewStudentPagePhDSupervisor,
)


class StudentPageProxy(StudentPage):
    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        super(StudentPageProxy, self).__init__(*args, **kwargs)
        self.parent_id = self.get_parent().id

    @property
    def is_phd_page(self):
        return self.degree_qualification in ['phd', 'researchstudent']

    @property
    def is_mphil_page(self):
        return self.degree_qualification == 'mphil'

    @property
    def is_ma_page(self):
        return self.degree_qualification == 'ma'

    @property
    def is_in_show(self):
        return self.parent_id == 5255

    @property
    def is_in_rca_now(self):
        return self.parent_id == 36

    @property
    def is_in_research_students(self):
        return self.parent_id == 3970


class StudentMigration(object):
    def __init__(self, save=False, index_page=None, migrate=True, update_references=False):
        self.skipped_students = []
        self.index_page = Page.objects.get(pk=index_page) if index_page else None
        self.save = save and self.index_page
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

    def migrate_student_pages(self, name, ma_page, mphil_research_page, phd_research_page, mphil_show_page, phd_show_page):
        pages = [page for page in [ma_page, mphil_research_page, phd_research_page, mphil_show_page, phd_show_page] if page]
        most_recent = sorted(pages, key=lambda page: page.degree_year)[-1]

        mphil_pages = [page for page in [mphil_research_page, mphil_show_page] if page]
        phd_pages = [page for page in [phd_research_page, phd_show_page] if page]
        mphil_page_research = mphil_research_page or mphil_show_page
        phd_page_research = phd_research_page or phd_show_page
        mphil_page_show = mphil_show_page or mphil_research_page
        phd_page_show = phd_show_page or phd_research_page

        # Create new page
        new_page = NewStudentPage()
        new_page.title = name
        new_page.slug = slugify(name)
        new_page.live = most_recent.live
        new_page.has_unpublished_changes = not most_recent.live
        new_page.owner = None
        for page in pages:
            new_page.owner = new_page.owner or page.owner

        # General info
        new_page.first_name = most_recent.first_name
        new_page.last_name = most_recent.last_name
        new_page.profile_image = most_recent.profile_image
        new_page.statement = most_recent.statement
        new_page.twitter_handle = most_recent.student_twitter_feed
        new_page.funding = '; '.join([page.funding for page in pages if page.funding])
        new_page.feed_image = most_recent.feed_image
        new_page.show_on_homepage = most_recent.show_on_homepage

        # MA info
        if ma_page:
            new_page.ma_school = ma_page.school
            new_page.ma_programme = ma_page.programme
            new_page.ma_graduation_year = ma_page.graduation_year or ma_page.degree_year
            new_page.ma_specialism = ma_page.specialism
            new_page.show_work_type = ma_page.work_type
            new_page.show_work_location = ma_page.work_location
            new_page.show_work_description = ma_page.work_description
            new_page.ma_in_show = ma_page.is_in_show

        # MPhil info
        if mphil_pages:
            new_page.mphil_school = mphil_page_research.school
            new_page.mphil_programme = mphil_page_research.programme
            new_page.mphil_start_year = mphil_page_research.degree_year
            new_page.mphil_graduation_year = mphil_page_research.graduation_year
            #research_dissertation_title
            new_page.mphil_statement = mphil_page_show.work_description
            new_page.mphil_work_location = mphil_page_research.work_location
            new_page.mphil_in_show = mphil_page_show.is_in_show

        # PhD info
        if phd_pages:
            new_page.phd_school = phd_page_research.school
            new_page.phd_programme = phd_page_research.programme
            new_page.phd_start_year = phd_page_research.degree_year
            new_page.phd_graduation_year = phd_page_research.graduation_year
            #research_dissertation_title
            new_page.phd_statement = phd_page_show.work_description
            new_page.phd_work_location = phd_page_research.work_location
            new_page.phd_in_show = phd_page_show.is_in_show

        # General child objects
        for page in pages:
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

        # MA child objects
        if ma_page:
            for carousel_item in ma_page.carousel_items.all():
                new_page.show_carousel_items.add(NewStudentPageShowCarouselItem(
                    image=carousel_item.image,
                    overlay_text=carousel_item.overlay_text,
                    link=carousel_item.link,
                    link_page=carousel_item.link_page,
                    embedly_url=carousel_item.embedly_url,
                    poster_image=carousel_item.poster_image,
                ))

            for collaborator in ma_page.collaborators.all():
                new_page.show_collaborators.add(NewStudentPageShowCollaborator(name=collaborator.name))

            for sponsor in ma_page.sponsor.all():
                new_page.show_sponsors.add(NewStudentPageShowSponsor(name=sponsor.name))

        # MPhil child objects
        for page in mphil_pages:
            for carousel_item in page.carousel_items.all():
                new_page.mphil_carousel_items.add(NewStudentPageMPhilCarouselItem(
                    image=carousel_item.image,
                    overlay_text=carousel_item.overlay_text,
                    link=carousel_item.link,
                    link_page=carousel_item.link_page,
                    embedly_url=carousel_item.embedly_url,
                    poster_image=carousel_item.poster_image,
                ))

            for collaborator in page.collaborators.all():
                new_page.mphil_collaborators.add(NewStudentPageMPhilCollaborator(name=collaborator.name))

            for sponsor in page.sponsor.all():
                new_page.mphil_sponsors.add(NewStudentPageMPhilSponsor(name=sponsor.name))

            for supervisor in page.supervisors.all():
                new_page.mphil_supervisors.add(NewStudentPageMPhilSupervisor(supervisor=supervisor.supervisor, supervisor_other=supervisor.supervisor_other))

        # PhD child objects
        if page in phd_pages:
            for carousel_item in page.carousel_items.all():
                new_page.phd_carousel_items.add(NewStudentPagePhDCarouselItem(
                    image=carousel_item.image,
                    overlay_text=carousel_item.overlay_text,
                    link=carousel_item.link,
                    link_page=carousel_item.link_page,
                    embedly_url=carousel_item.embedly_url,
                    poster_image=carousel_item.poster_image,
                ))

            for collaborator in page.collaborators.all():
                new_page.phd_collaborators.add(NewStudentPagePhDCollaborator(name=collaborator.name))

            for sponsor in page.sponsor.all():
                new_page.phd_sponsors.add(NewStudentPagePhDSponsor(name=sponsor.name))

            for supervisor in page.supervisors.all():
                new_page.phd_supervisors.add(NewStudentPagePhDSupervisor(supervisor=supervisor.supervisor, supervisor_other=supervisor.supervisor_other))

        # Save new page
        if self.save:
            # Add new page into tree
            self.index_page.add_child(new_page)

            # Save revision
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
                # Get pages
                ma_page = None
                mphil_research_page = None
                phd_research_page = None
                mphil_show_page = None
                phd_show_page = None
                error = False
                for page in pages:
                    # MA page
                    if page.is_ma_page:
                        if ma_page:
                            # Take latest ma page
                            if ma_page.degree_year < page.degree_year:
                                ma_page = page
                        else:
                            ma_page = page

                    # MPhil page
                    if page.is_mphil_page:
                        if page.is_in_show:
                            if mphil_show_page:
                                error = True
                                break
                            mphil_show_page = page
                        else:
                            if mphil_research_page:
                                error = True
                                break
                            mphil_research_page = page

                    # PHD page
                    if page.is_phd_page:
                        if page.is_in_show:
                            if phd_show_page:
                                error = True
                                break
                            phd_show_page = page
                        else:
                            if phd_research_page:
                                error = True
                                break
                            phd_research_page = page

                # Check for error
                if not error:
                    print "Migrating: " + student
                    new_page = self.migrate_student_pages(student, ma_page, mphil_research_page, phd_research_page, mphil_show_page, phd_show_page)
                else:
                    print "Skipping: " + student
                    self.skipped_students.append(student)

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
