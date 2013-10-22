from lxml import etree as ET
from rca.models import StaffPage, RcaImage, StaffIndex, StaffPageRole
from django.utils.dateparse import parse_date
from django.core.files import File
from importer.import_utils import richtext_from_elem, text_from_elem, make_slug, check_length
from importer import constants
import datetime
import urllib2
from bs4 import BeautifulSoup


# TODO
# All staff are Acedemic
# Look into underscores issue
# "Current and recent research", "practise" and "research interests" are like the placeholders
# Carousel content is all images except those associated with a research item
# All child pages except for the placeholder pages are research items
# Remove profile pictures
# Cleanup & Better error checking


PATH = 'importer/data/export_staff_profiles.xml'
IMAGE_PATH = 'importer/data/export_staff_images/'
STAFF_INDEX_PAGE = StaffIndex.objects.get(slug='staff-index-page')

def import_texts(element):
    errors = {}

    html = ""
    for text in element.findall('text'):
        text_title, errors["title"] = text_from_elem(text, 'title', length=255, textify=True)
        text_content, errors["content"] = text_from_elem(text, 'content', length=255)
        html = "".join([html, "<b>", text_title, "</b>", text_content, "<hr>"])
    return html, errors

def import_image(element):
    errors = {}

    # Get image info
    image_contentid = element.attrib['contentid']
    image_filename, errors['filename'] = text_from_elem(element, 'filename', length=255, textify=True)
    image_caption, errors['caption'] = text_from_elem(element, 'caption', length=255, textify=True)

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

    # Load image file
    try:
        with File(open(IMAGE_PATH + image_filename.encode('utf-8'), 'r')) as f:
            if image.id:
                image.delete()
            image.file = f
            image.save()
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
        print repr(image_filename)
    except ValueError:
        print "Could not convert data to an integer."
    except:
        import sys
        print "Unexpected error:", sys.exc_info()[0]
        raise

    return image, errors


def import_staff_research_childpage(staffpage, element):
    errors = {}

    # Get page info
    page_contentid = element.attrib['contentid']
    page_title, errors['title'] = text_from_elem(element, 'title', length=255, textify=True)
    page_texts_element = element.find('texts')

    # If the page is about Publications or External Collaborations, add it into the staffpage
    if page_title == "Publications, Exhibitions & Other Outcomes":
        staffpage.publications_exhibtions_and_other_outcomes_placeholder, errors['texts'] = import_texts(page_texts_element)
    elif page_title == "External Collaborations":
        staffpage.external_collaborations_placeholder, errors['texts'] = import_texts(page_texts_element)

    return errors


def import_staff_researchpage(staffpage, element):
    errors = {}

    # Get page info
    page_contentid = element.attrib['contentid']
    page_title, errors['title'] = text_from_elem(element, 'title', length=255, textify=True)
    page_texts_element = element.find('texts')

    # If the page is about Publications or External Collaborations, add it into the staffpage
    if page_title == "Publications, Exhibitions & Other Outcomes":
        staffpage.publications_exhibtions_and_other_outcomes_placeholder, errors['texts'] = import_texts(page_texts_element)
    elif page_title == "External Collaborations":
        staffpage.external_collaborations_placeholder, errors['texts'] = import_texts(page_texts_element)

    return errors


def import_staff(element):
    errors = {}

    # Basic info
    staff_contentid = element.attrib['contentid']
    staff_title, errors['title'] = text_from_elem(element, 'title', length=255, textify=True)
    staff_name, errors['name'] = text_from_elem(element, 'staffname', length=255, textify=True)
    staff_programme, errors['programme'] = text_from_elem(element, 'programme', length=255, textify=True)
    staff_statement, errors['statement'] = text_from_elem(element, 'statement', textify=True)
    staff_biography, errors['biography'] = text_from_elem(element, 'biography', textify=True)
    staff_school, errors['school'] = text_from_elem(element, 'school', length=255, textify=True)
    staff_editorialreference, errors['editorialreference'] = text_from_elem(element, 'editorialreference', length=255, textify=True)

    # Emails
    staff_emails = []
    emails_element = element.find('emails')
    if emails_element is not None:
        for email in emails_element.findall('email'):
            staff_emails.append(email.text)

    # URLs
    staff_urls = []
    urls_element = element.find('urls')
    if urls_element is not None:
        for url in urls_element.findall('url'):
            staff_urls.append(url.text)

    # Supervised students
    staff_supervisedstudents = []
    supervisedstudents_element = element.find('supervisedstudents')
    if supervisedstudents_element is not None:
        for supervisedstudent in supervisedstudents_element.findall('supervisedstudent'):
            supervised_student = supervisedstudent.text
            if supervised_student is not None:
                staff_supervisedstudents.append(supervisedstudent.text)

    # Split name into first name, last name and title
    name_split = staff_name.split()
    if name_split[0] == "Professor" or name_split[0] == "Dr" or name_split[0] == "Sir":
        staff_titleprefix = name_split[0]
        staff_firstname = name_split[1]
        staff_lastname = " ".join(name_split[2:])
    else:
        staff_titleprefix = ""
        staff_firstname = " ".join(name_split[:1])
        staff_lastname = " ".join(name_split[1:])

    # Remove "Programme" from staff_programme if it is there
    programme_split = staff_programme.split()
    if programme_split[-1] == "Programme":
        staff_programme = " ".join(programme_split[:-1])

    # Slugs
    staff_programme_slug = constants.PROGRAMMES.get(staff_programme, "")
    staff_school_slug = constants.SCHOOLS.get(staff_programme, "")

    # Create page for staff member
    try:
        staffpage = StaffPage.objects.get(rca_content_id=staff_contentid)
    except StaffPage.DoesNotExist:
        staffpage = StaffPage()
        staffpage.rca_content_id = staff_contentid
    staffpage.title = staff_name
    staffpage.school = staff_school_slug
    staffpage.intro = staff_statement
    staffpage.biography = staff_biography
    staffpage.show_on_homepage = False
    staffpage.show_on_programme_page = False
    staffpage.title_prefix = staff_titleprefix
    staffpage.first_name = staff_firstname
    staffpage.last_name = staff_lastname
    if len(staff_supervisedstudents) > 0:
        staffpage.supervisedStudentOther = ", ".join(staff_supervisedstudents)
    staffpage.slug = make_slug(staffpage)
    if staffpage.id:
        staffpage.save()
    else:
        STAFF_INDEX_PAGE.add_child(staffpage)

    # Create role
    try:
        staffpagerole = StaffPageRole.objects.get(page=staffpage)
    except StaffPageRole.DoesNotExist:
        staffpagerole = StaffPageRole()
        staffpagerole.page=staffpage

    staffpagerole.title = staff_title
    staffpagerole.school = staff_school_slug
    staffpagerole.programme = staff_programme_slug
    staffpagerole.save()

    # Images
    staff_images = []
    images_element = element.find('images')
    if images_element is not None:
        for image in images_element.findall('image'):
            theimage, error = import_image(image)
            staff_images.append(theimage)

    # Set first found image as profile picture
    if len(staff_images) > 0:
        staffpage.profile_image = staff_images[0]

    # Research pages
    researchpages_element = element.find('researchpages')
    if researchpages_element is not None:
        for researchpage in researchpages_element.findall('page'):
            import_staff_researchpage(staffpage, researchpage)

        # Research child pages
        research_childpages_element = researchpages_element.find('childpages')
        if research_childpages_element is not None:
            for childpage in research_childpages_element.findall('page'):
                import_staff_research_childpage(staffpage, childpage)

    # Resave page
    staffpage.save()

    return errors


def import_department(element):
    errors = {}

    # Basic info
    department_contentid = element.find('departmentname').attrib['contentid']
    department_name, errors['name'] = text_from_elem(element, 'departmentname', length=255)

    # Staff
    for staff in element.findall('staff'):
        import_staff(staff)

    return errors


def doimport(**kwargs):
    root = ET.parse(path).getroot()

    # Departments
    for department in root.findall('department'):
        import_department(department)
