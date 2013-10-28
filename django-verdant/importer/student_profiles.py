# coding=utf-8

from lxml import etree as ET
from rca.models import StudentPage, StudentPageCarouselItem, RcaImage, ResearchItem, ResearchItemCarouselItem, ResearchItemCreator, ResearchInnovationPageCurrentResearch
from core.models import Page
from django.utils.dateparse import parse_date
from django.core.files import File
from importer.import_utils import richtext_from_elem, text_from_elem, make_slug, check_length
from importer import constants
import datetime
import urllib2
from bs4 import BeautifulSoup


IGNORED_NAMES = [
    u"Research Alumni 1995–2010",
    "Research at the Royal College of Art",
    "Introductory Bibliography",
    "Information for Research Staff",
    "Definitions of Research",
    "Guidelines on Bibliographical References",
    "Good Research Practice",
    "Research Student Progression",
    "Guide to Libraries",
    "Presenting Your Research",
]


def cleanup_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove HR tags
    for hr in soup.find_all("hr"):
        hr.decompose()

    return unicode(soup)


class StudentProfilesImporter(object):
    def __init__(self, **kwargs):
        self.save = kwargs.get("save", False)
        self.path = kwargs.get("path", "importer/data/export_student_profiles.xml")
        self.image_path = kwargs.get("image_path", "importer/data/export_student_images/")
        self.student_index = kwargs.get("student_index", "students")
        self.research_index = kwargs.get("research_index", "current-research")
        self.staff_index = kwargs.get("staff_index", "staff")


    def import_texts(self, element):
        errors = {}

        html = ""
        first_text = True
        for text in element.findall('text'):
            if first_text:
                first_text = False
            else:
                html = "".join([html, "<hr>"])
            text_title, errors["title"] = text_from_elem(text, 'title', length=255)
            text_content, errors["content"] = text_from_elem(text, 'content')

            html = "".join([html, "<b>", text_title, "</b>", cleanup_html(text_content)])

        return html, errors


    def import_image(self, element):
        errors = {}

        # Get image info
        image_contentid = element.attrib['contentid']
        image_filename, errors['filename'] = text_from_elem(element, 'filename', length=255, textify=True)
        image_caption, errors['caption'] = text_from_elem(element, 'caption', length=255)

        image_metadata = element.find('imagemetadata')
        image_title, errors['title'] = text_from_elem(image_metadata, 'title', length=255, textify=True)
        image_creator, errors['creator'] = text_from_elem(image_metadata, 'creator', length=255, textify=True)
        image_media, errors['media'] = text_from_elem(image_metadata, 'media', length=255, textify=True)
        image_photographer, errors['photographer'] = text_from_elem(image_metadata, 'photographer', length=255, textify=True)
        image_rights, errors['rights'] = text_from_elem(image_metadata, 'rights', length=255, textify=True)

        # Create image
        try:
            image = RcaImage.objects.get(rca_content_id=image_contentid)
        except RcaImage.DoesNotExist:
            image = RcaImage()
            image.rca_content_id = image_contentid

        image.title = image_title
        image.alt = image_caption
        image.creator = image_creator
        image.medium = image_media
        image.photographer = image_photographer
        image.permission = image_rights

        if self.save:
            # Load image file
            if not image.id:
                try:
                    with File(open(self.image_path + image_filename.encode('utf-8'), 'r')) as f:
                        image.file = f
                        image.save()
                except IOError as e:
                    print "I/O error({0}): {1}".format(e.errno, e.strerror)
                    print repr(image_filename)
                    return None, None
                except ValueError:
                    print "Could not convert data to an integer."
                    return None, None
                except:
                    import sys
                    print "Unexpected error:", sys.exc_info()[0]
                    raise
            else:
                image.save()

        return image, errors


    def import_student_researchpage(self, studentpage, element):
        errors = {}

        # Get page info
        page_contentid = element.attrib["contentid"]
        page_title, errors["title"] = text_from_elem(element, "title", length=255, textify=True)
        page_texts, errors["texts"] = self.import_texts(element.find("texts"))

        # Create research item
        try:
            researchitem = ResearchItem.objects.get(rca_content_id=page_contentid)
        except ResearchItem.DoesNotExist:
            researchitem = ResearchItem()
            researchitem.rca_content_id = page_contentid
        researchitem.title = page_title
        researchitem.research_type = "student"
        researchitem.description = page_texts
        researchitem.school = studentpage.school
        researchitem.programme = studentpage.programme
        researchitem.slug = make_slug(researchitem)

        if self.save:
            if researchitem.id:
                researchitem.save()
            else:
                self.research_index_page.add_child(researchitem)

            # Link to creator
            ResearchItemCreator.objects.get_or_create(page=researchitem, person=studentpage)

        # Get carousel images
        images_element = element.find("images")
        if images_element is not None:
            for image in images_element.findall("image"):
                # Import the image
                theimage, error = self.import_image(image)

                # Add to carousel
                if theimage is not None and self.save:
                    ResearchItemCarouselItem.objects.get_or_create(page=researchitem, image=theimage)

        return errors

    def find_staff_page(self, name):
        # Get list of potential names
        names = [title + " " + name for title in ["Dr", "Professor", "Sir"]]
        names.append(name)

        # Slugify them
        slugs = map(lambda slug: slug.strip(" ").replace("'", "").lower().replace(" ", "-"), names)

        # Search the database
        for slug in slugs:
            try:
                staffpage = self.staff_index_page.get_children().get(slug=slug).specific
                return staffpage
            except:
                continue

        return None

    def import_student(self, element):
        errors = {}

        # Basic info
        student_contentid = element.attrib["contentid"]
        student_title, errors["title"] = text_from_elem(element, "title", length=255, textify=True)
        student_name, errors["name"] = text_from_elem(element, "staffname", length=255, textify=True)
        student_programme, errors["programme"] = text_from_elem(element, "programme", length=255, textify=True)
        student_biography, errors["biography"] = text_from_elem(element, "biography")
        student_school, errors["school"] = text_from_elem(element, "school", length=255, textify=True)
        student_editorialreference, errors["editorialreference"] = text_from_elem(element, "editorialreference", length=255, textify=True)

        # If name is in ignore list, skip it
        if student_name in IGNORED_NAMES:
            return

        # Supervisor
        student_supervisor = None
        supervisedstudents_element = element.find("supervisedstudents")
        if supervisedstudents_element is not None:
            student_supervisor_name = supervisedstudents_element.find("supervisedstudent").text

            # Get page for supervisor
            student_supervisor = self.find_staff_page(student_supervisor_name)

        # Cleanup  biography
        student_biography = cleanup_html(student_biography)

        # Split name into first name, last name and title
        name_split = student_name.split()
        student_firstname = " ".join(name_split[:1])
        student_lastname = " ".join(name_split[1:])

        # Remove "Programme" from student_programme if it is there
        student_programme_split = student_programme.split()
        if len(student_programme_split) > 0:
            if student_programme_split[-1] == "Programme" or student_programme_split[-1] == "Programmes":
                student_programme = " ".join(student_programme_split[:-1])

        # Remove "\r" from beginning of student_programme if it is there
        if student_programme and student_programme[:2] == "\\r":
            student_programme = student_programme[2:]

        # Remove \n from beginning and end of student_school if it is there
        if student_school and student_school[:2] == "\\n":
            student_school = student_school[2:]
        if student_school and student_school[-2:] == "\\n":
            student_school = student_school[:-2]

        # Slugs
        student_programme_slug = constants.PROGRAMMES.get(student_programme, "")
        student_school_slug = constants.SCHOOLS.get(student_school, "")



        # Create page for student
        try:
            studentpage = StudentPage.objects.get(rca_content_id=student_contentid)
        except StudentPage.DoesNotExist:
            studentpage = StudentPage()
            studentpage.rca_content_id = student_contentid
        studentpage.title = student_name
        studentpage.school = student_school_slug
        studentpage.programme = student_programme_slug
        studentpage.degree_qualification = ""
        studentpage.degree_subject = ""
        studentpage.degree_year = ""
        studentpage.statement = student_biography
        studentpage.show_on_homepage = False
        studentpage.show_on_programme_page = False
        studentpage.first_name = student_firstname
        studentpage.last_name = student_lastname
        studentpage.supervisor = student_supervisor
        studentpage.slug = make_slug(studentpage)
        if self.save:
            if studentpage.id:
                studentpage.save()
            else:
                self.student_index_page.add_child(studentpage)



        # Images
        images_element = element.find("images")
        if images_element is not None:
            for image in images_element.findall("image"):
                # Import the image
                theimage, error = self.import_image(image)

                if theimage is not None and self.save:
                    # Add to carousel
                    StudentPageCarouselItem.objects.get_or_create(page=studentpage, image=theimage)



        # Research pages
        researchpages_element = element.find("researchpages")
        if researchpages_element is not None:
            for researchpage in researchpages_element.findall("page"):
                self.import_student_researchpage(studentpage, researchpage)

            # Research child pages
            research_childpages_element = researchpages_element.find("childpages")
            if research_childpages_element is not None:
                for childpage in research_childpages_element.findall("page"):
                    self.import_student_researchpage(studentpage, childpage)


        # Resave page
        if self.save:
            studentpage.save()


    def import_department(self, element):
        errors = {}

        # Basic info
        department_contentid = element.find("departmentname").attrib["contentid"]
        department_name, errors["name"] = text_from_elem(element, "departmentname", length=255)

        # Students
        for student in element.findall("staff"):
            self.import_student(student)

    def doimport(self):
        # Parse XML document and get root element
        self.tree = ET.parse(self.path)
        self.root = self.tree.getroot()

        # Get index pages
        self.student_index_page = Page.objects.get(slug=self.student_index).specific
        self.research_index_page = Page.objects.get(slug=self.research_index).specific
        self.staff_index_page = Page.objects.get(slug=self.staff_index).specific

        # Departments
        for department in self.root.findall("department"):
            self.import_department(department)


def doimport():
    importer = StudentProfilesImporter(save=True)
    importer.doimport()