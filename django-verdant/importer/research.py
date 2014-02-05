from importer.import_utils import make_slug
from rca.models import ResearchItem, ResearchItemCreator
from wagtail.wagtailcore.models import Page
import os
import httplib2
import json


WORK_TYPES_CHOICES = {
    #('journalarticle', 'Journal Article'),
    'article': 'journalarticle',
    #('thesis', 'Thesis'),
    'thesis': 'thesis',
    #('booksection', 'Book Section'),
    'book_section': 'booksection',
    #('monograph', 'Monograph'),
    'monograph': 'monograph',
    #('printepublication', 'Printed Publication'),
    'printpub': 'printepublication',
    'book': 'printepublication',
    #('conferenceorworkshop', 'Conference or Workshop'),
    'conference_item': 'conferenceorworkshop',
    #('artordesignobject', 'Art or design object'),
    'artefact': 'artordesignobject',
    #('showexhibitionorevent', 'Show, Exhibition or Event'),
    'exhibition': 'showexhibitionorevent',
    #('teachingresource', 'Teaching Resource'),
    'teaching_resource': 'teachingresource',
    #('residency', 'Residency'),
    #('other', 'Other (enter below)'),
    'other': 'other',
}


DIVISION_SCHOOL_MAPPING = {
    "s1": "schoolofarchitecture",
    "s2": "schoolofcommunication",
    "s3": "schoolofdesign",
    "s4": "schoolofmaterial",
    "s5": "schooloffineart",
    "s6": "schoolofhumanities",
    "rc1": "helenhamlyn",
}


def text_to_html(text):
    paragraphs = text.split("\r\n")
    html = ""
    for paragraph in paragraphs:
        html = "".join([html, "<p>", paragraph, "</p>"])
    return html


class ResearchImporter(object):
    def __init__(self, **kwargs):
        self.save = kwargs.get("save", False)
        self.link_creators = kwargs.get("link_creators", False)
        self.cache_directory = kwargs.get("cache_directory", "importer/data/research/")
        self.student_index = kwargs.get("student_index", "research-students")
        self.research_index = kwargs.get("research_index", "current-research")
        self.staff_index = kwargs.get("staff_index", "staff")
        self.http = httplib2.Http()

        # Create cache directories
        try:
            os.makedirs(self.cache_directory)
        except OSError: # Directory alredy exists
            pass

    def find_person_page(self, person_name):
        titles = ["Dr", "Professor", "Sir"]
        slug_separators = ['', '-', '_']

        # Get list of potential names
        names = [title + " " + person_name for title in titles]
        names.append(person_name)

        # Replace dashes with spaces
        names = [name.replace("-", " ") for name in names]

        # Slugify them
        slugs = []
        for separator in slug_separators:
            slugs.extend(map(lambda slug: slug.strip(" ").replace("'", "").lower().replace(" ", separator), names))

        # Search the staff pages
        for slug in slugs:
            try:
                return self.staff_index_page.get_children().get(slug=slug).specific
            except:
                continue

        # Search the student pages
        for slug in slugs:
            try:
                return self.student_index_page.get_children().get(slug=slug).specific
            except:
                continue

        return None

    def add_researchitemcreator(self, researchitem, creator_name):
        # Find creator page
        creator_page = self.find_person_page(creator_name)

        # Add research item creator
        if self.save:
            if creator_page is not None:
                ResearchItemCreator.objects.get_or_create(page=researchitem, person=creator_page)
            else:
                ResearchItemCreator.objects.get_or_create(page=researchitem, manual_person_name=creator_name)

    def import_researchitem(self, researchitem):
        # Get basic info
        researchitem_eprintid = researchitem["eprintid"]
        researchitem_title = researchitem["title"]
        researchitem_abstract = researchitem.get("abstract", "")
        researchitem_type = researchitem["type"]
        researchitem_department = researchitem.get("department", "")
        researchitem_divisions = researchitem.get("divisions", [])

        # Get year
        if "date" in researchitem:
            # First 4 characters are always the year
            researchitem_year = str(researchitem["date"])[:4]
        elif "datestamp" in researchitem:
            # First 4 characters are always the year
            researchitem_year = str(researchitem["datestamp"])[:4]
        else:
            print "NO DATE"
            researchitem_year = ""

        # Get school
        researchitem_school = ""
        for division in researchitem_divisions:
            if division in DIVISION_SCHOOL_MAPPING:
                researchitem_school = DIVISION_SCHOOL_MAPPING[division]
                break

        # Convert description to HTML
        researchitem_abstract = text_to_html(researchitem_abstract)

        # Subtitle
        if researchitem_type == 'book_section':
            researchitem_subtitle = researchitem['book_title']
        elif researchitem_type == 'conference_item':
            researchitem_subtitle = researchitem['event_title']
        else:
            researchitem_subtitle = ''

        # Create researchitem page
        try:
            researchitempage = ResearchItem.objects.get(eprintid=researchitem_eprintid)

            # Find latest revision of researchitem
            researchitem_latest_revision = researchitempage.get_latest_revision_as_page()
        except ResearchItem.DoesNotExist:
            researchitempage = ResearchItem(eprintid=researchitem_eprintid)
            researchitem_latest_revision = None

        # Set values
        researchitempage.title = researchitem_title
        researchitempage.subtitle = researchitem_subtitle
        researchitempage.ref = True
        researchitempage.research_type = "staff"
        researchitempage.year = researchitem_year
        researchitempage.description = researchitem_abstract
        researchitempage.work_type = WORK_TYPES_CHOICES[researchitem_type]
        researchitempage.school = researchitem_school
        researchitempage.show_on_homepage = False
        researchitempage.slug = make_slug(researchitempage)

        # Save researchitem
        if self.save:
            if researchitempage.id:
                researchitempage.save()
            else:
                self.research_index_page.add_child(researchitempage)

        # Update latest revision
        if researchitem_latest_revision is not None:
            researchitem_latest_revision.title = researchitem_title
            researchitem_latest_revision.subtitle = researchitem_subtitle
            researchitem_latest_revision.ref = True
            researchitem_latest_revision.research_type = "staff"
            researchitem_latest_revision.year = researchitem_year
            researchitem_latest_revision.description = researchitem_abstract
            researchitem_latest_revision.work_type = WORK_TYPES_CHOICES[researchitem_type]
            researchitem_latest_revision.school = researchitem_school
            researchitem_latest_revision.show_on_homepage = False

            # Save latest revision
            if self.save:
                researchitem_latest_revision.save_revision()

        # Link creators
        if self.link_creators:
            for creator in researchitem["creators"]:
                creator_name = creator["name"]["given"] + " " + creator["name"]["family"]
                self.add_researchitemcreator(researchitempage, creator_name)

    def get_research_file(self, eprintid):
        # Attempt to load from cache
        filename = self.cache_directory + eprintid + ".json"
        try:
            return open(filename, "r")
        except IOError:
            pass

        # Download instaed
        url = "http://researchonline.rca.ac.uk/cgi/export/eprint/%(eprintid)s/JSON/rca-eprint-%(eprintid)s.js" % {
            "eprintid": eprintid,
        }
        status, response = self.http.request(url)
        if status["status"] == "200":
            # Save file to disk
            f = open(filename, "w")
            f.write(response)
            f.close()

            # Return new handle to file
            return open(filename, "r")
        else:
            return None

    def import_researchitem_from_eprintid(self, eprintid):
        # Load file
        f = self.get_research_file(eprintid)

        # Check file
        if f is None:
            print "Cannot get file for " + eprintid
            return

        # Load contents
        researchitem = json.loads(f.read())

        # Import it
        self.import_researchitem(researchitem)

    def run(self, eprintid_list):
        # Get index pages
        self.student_index_page = Page.objects.get(slug=self.student_index).specific
        self.research_index_page = Page.objects.get(slug=self.research_index).specific
        self.staff_index_page = Page.objects.get(slug=self.staff_index).specific

        # Loop through eprint ids
        for eprintid in eprintid_list:
            self.import_researchitem_from_eprintid(str(eprintid))


def run(save=False, link_creators=False, eprints_file='importer/data/research_eprints.json'):
    # Load json file
    with open(eprints_file, 'r') as f:
        eprintid_list = json.load(f)

    # Import
    importer = ResearchImporter(save=save, link_creators=link_creators)
    importer.run(eprintid_list)
