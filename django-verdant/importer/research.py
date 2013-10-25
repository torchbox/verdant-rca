from importer.import_utils import richtext_from_elem, text_from_elem, make_slug, check_length
from importer.data.staffdata import staff_data
from importer import constants
from django.utils.dateparse import parse_date
from rca.models import ResearchItem, ResearchItemCreator, StaffIndex, CurrentResearchPage
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


DIVISION_SCHOOL_MAPPING = {
    "s1": "schoolofarchitecture",
    "s2": "schoolofcommunication",
    "s3": "schoolofdesign",
    "s4": "schoolofmaterial",
    "s5": "schooloffineart",
    "s6": "schoolofhumanities",
}


def text_to_html(text):
    paragraphs = text.split("\r\n")
    html = ""
    for paragraph in paragraphs:
        html = "".join([html, "<p>", paragraph, "</p>"])
    return html


class ResearchImporter(object):
    def __init__(self, **kwargs):
        self.save = kwargs.get("save", True)
        self.cache_directory = kwargs.get("cache_directory", "importer/data/research/")
        self.research_cache_directory = self.cache_directory + "research/"
        self.student_index = kwargs.get("student_index", "students")
        self.research_index = kwargs.get("research_index", "current-research")
        self.staff_index = kwargs.get("staff_index", "staff")
        self.http = httplib2.Http()

        # Create cache directories
        try:
            os.makedirs(self.research_cache_directory)
        except OSError: # Directory alredy exists
            pass


    def find_person_page(self, person_name):
        # Get list of potential names
        names = [title + " " + person_name for title in ["Dr", "Professor", "Sir"]]
        names.append(person_name)

        # Slugify them
        slugs = map(lambda slug: slug.strip(" ").replace("'", "").lower().replace(" ", "-"), names)

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
        # TODO: Use division instead
        researchitem_school = ""
        if researchitem_department in constants.SCHOOLS:
            researchitem_school = constants.SCHOOLS[researchitem_department]

        # Convert description to HTML
        researchitem_abstract = text_to_html(researchitem_abstract)

        # Create researchitem page
        try:
            researchitempage = ResearchItem.objects.get(eprintid=researchitem_eprintid)
        except ResearchItem.DoesNotExist:
            researchitempage = ResearchItem(eprintid=researchitem_eprintid)

        # Set values
        researchitempage.title = researchitem_title
        researchitempage.ref = True
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
                self.research_index_page.add_child(researchitempage)

        for creator in researchitem["creators"]:
            creator_name = creator["name"]["given"] + " " + creator["name"]["family"]
            self.add_researchitemcreator(researchitempage, creator_name)

    def download_research(self, username, filename):
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

    def import_research(self, user):
        # Ignore users with REF=FALSE
        #if user["REF"] == "FALSE":
        #    return

        # Get username
        username = user["sAMAccountName"]

        # Attempt to get research from cache
        filename = self.research_cache_directory + username + ".json"
        try:
            f = open(filename, "r")
        except IOError:
            # Not in cache, download instead
            if self.download_research(username, filename):
                f = open(filename, "r")
            else:
                print "Unable to download research info for " + username
                return

        # Load file
        researchitems = json.loads(f.read())

        # Get researchitems
        print "Found " + str(len(researchitems)) + " research items for " + username
        for researchitem in researchitems:
            self.import_researchitem(researchitem)

    def doimport(self, staff_data):
        # Get index pages
        self.student_index_page = Page.objects.get(slug=self.student_index).specific
        self.research_index_page = Page.objects.get(slug=self.research_index).specific
        self.staff_index_page = Page.objects.get(slug=self.staff_index).specific

        # Iterate through staff list
        for staff in staff_data:
            self.import_research(staff)


def doimport():
    # Import
    importer = ResearchImporter(save=True)
    importer.doimport(staff_data)
