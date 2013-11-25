from importer.import_utils import richtext_from_elem, text_from_elem, make_slug, check_length
from importer import constants
from django.utils.dateparse import parse_date
from rca.models import ResearchItem, ResearchItemCreator, StaffIndex, CurrentResearchPage
from core.models import Page
import os
import httplib2
import json
from collections import namedtuple
import csv
import re


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
        self.research_csv_filename = kwargs.get("research_csv_filename", "importer/data/research.csv")
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

        # Create researchitem page
        try:
            researchitempage = ResearchItem.objects.get(eprintid=researchitem_eprintid)
        except ResearchItem.DoesNotExist:
            researchitempage = ResearchItem(eprintid=researchitem_eprintid)

        # Set values
        researchitempage.title = researchitem_title
        researchitempage.ref = True
        researchitempage.research_type = "staff"
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
        with self.get_research_file(eprintid) as f:
            # Check file
            if f is None:
                print "Cannot get file for " + eprintid
                return

            # Load contents
            researchitem = json.loads(f.read())

            # Import it
            self.import_researchitem(researchitem)

    def doimport(self):
        # Get index pages
        self.student_index_page = Page.objects.get(slug=self.student_index).specific
        self.research_index_page = Page.objects.get(slug=self.research_index).specific
        self.staff_index_page = Page.objects.get(slug=self.staff_index).specific

        # Load research
        ResearchRecord = namedtuple("ResearchRecord", "author, output_type, title, ref_url")
        research_csv = csv.reader(open(self.research_csv_filename, "rb"))

        # Expression for finding eprintids in ref urls
        eprint_expr = re.compile(r"^(?:http|https)://researchonline.rca.ac.uk/(\d+)/")

        # Iterate through research
        for research_line in research_csv:
            # Load research item into named tuple
            research = ResearchRecord._make(research_line)

            # Work out the eprintid
            match = eprint_expr.match(research.ref_url)
            if match:
                eprintid = match.group(1)
                self.import_researchitem_from_eprintid(eprintid)
            else:
                print "Cannot find eprintid in " + research.ref_url
                continue


def doimport():
    # Import
    importer = ResearchImporter(save=True)
    importer.doimport()
