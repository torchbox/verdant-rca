from importer.import_utils import richtext_from_elem, text_from_elem, make_slug, check_length
from importer.data.staffdata import staff_data
from importer import constants
from django.utils.dateparse import parse_date
from rca.models import ResearchItem, StaffIndex, CurrentResearchPage
from core.models import Page
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


class ResearchImporter(object):
    def __init__(self, staff_index, research_index, **kwargs):
        self.staff_index = staff_index
        self.research_index = research_index
        self.cache_directory = kwargs.get("cache_directory", "importer/data/research/")
        self.save = kwargs.get("save", True)
        self.research_cache_directory = self.cache_directory + "research/"
        self.http = httplib2.Http()

        # Stats
        self.total_staff = 0
        self.ignored_staff = 0
        self.total_researchitems = 0

        # Create cache directories
        try:
            os.makedirs(self.research_cache_directory)
        except OSError: # Directory alredy exists
            pass

    def import_researchitem(self, staffpage, researchitem):
        self.total_researchitems += 1

        # Get basic info
        researchitem_eprintid = researchitem["eprintid"]
        researchitem_title = researchitem["title"]
        researchitem_abstract = researchitem.get("abstract", "")
        researchitem_type = researchitem["type"]
        researchitem_department = researchitem.get("department", "")

        # Get year
        researchitem_year = None
        if "date" in researchitem:
            researchitem_date = researchitem["date"]
            if isinstance(researchitem_date, basestring):
                try:
                    researchitem_year = str(parse_date(researchitem_date).year)
                except AttributeError:
                    researchitem_year = researchitem_date[0:4]
            elif isinstance(researchitem_date, int):
                researchitem_year = str(researchitem_date)

        # Get school
        researchitem_school = ""
        if researchitem_department in constants.SCHOOLS:
            researchitem_school = constants.SCHOOLS[researchitem_department]

        # Create researchitem page
        try:
            researchitempage = ResearchItem.objects.get(eprintid=researchitem_eprintid)
        except ResearchItem.DoesNotExist:
            researchitempage = ResearchItem(eprintid=researchitem_eprintid)

        # Set values
        researchitempage.title = researchitem_title
        researchitempage.year = researchitem_year
        researchitempage.description = researchitem_abstract
        researchitempage.work_type = WORK_TYPES_CHOICES[researchitem_type]
        researchitempage.school = researchitem_school
        researchitempage.slug = make_slug(researchitempage)

        # Save researchitem
        if self.save:
            if researchitempage.id:
                researchitempage.save()
            else:
                self.research_index.add_child(researchitempage)

            # Link to staff page
            ResearchItemCreator.objects.get_or_create(page=researchitempage, person=staffpage)

    def download_staff_research(self, username, filename):
        url = "http://researchonline.rca.ac.uk/cgi/search/archive/simple/export_rca_JSON.js?screen=Search&dataset=archive&_action_export=1&output=JSON&exp=0%%7C1%%7C%%7Carchive%%7C-%%7Cq%%3A%%3AALL%%3AIN%%3A%(username)s%%7C-%%7C&n=&cache=" % {
            "username": username,
        }
        status, response = self.http.request(url)
        if status["status"] == "200":
            f = open(filename, "w")
            f.write(response)
            f.close()
            return True
        else:
            return False

    def import_staff_research(self, staff):
        self.total_staff += 1

        # Get username
        staff_username = staff["sAMAccountName"]
        print staff_username

        # Attempt to get research from cache
        filename = self.research_cache_directory + staff_username + ".json"
        try:
            f = open(filename, "r")
        except IOError:
            # Not in cache, download instead
            if self.download_staff_research(staff_username, filename):
                f = open(filename, "r")
            else:
                print "Unable to download research info for " + staff_username
                return

        # Load file
        researchitems = json.loads(f.read())

        # Get staff page
        try:
            slug = (staff["givenName"] + " " + staff["sn"]).strip(" ").lower().replace(" ", "-")
            staffpage = self.staff_index.get_children().get(slug=slug).specific
            self.ignored_staff += 1
        except Page.DoesNotExist:
            print "Unable to find staff page for " + staff_username + ". Ignoring..."
            return

        # Download documents for each researchitem
        print "    Found " + str(len(researchitems)) + " research items"
        for researchitem in researchitems:
            self.import_researchitem(staffpage, researchitem)

    def doimport(self, staff_data):
        # Iterate through staff list
        for staff in staff_data:
            self.import_staff_research(staff)


def doimport():
    # Get indexes
    staff_index = StaffIndex.objects.get(slug="staff")
    research_index = CurrentResearchPage.objects.get(slug="current-research")

    # Import
    importer = ResearchImporter(staff_index, research_index, save=False)
    importer.doimport(staff_data)

    print importer.total_documents
    print importer.total_file_size
