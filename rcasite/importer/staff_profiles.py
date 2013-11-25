from lxml import etree as ET
from rca.models import StaffPage, StaffPageCarouselItem, RcaImage, StaffIndex, StaffPageRole, CurrentResearchPage, ResearchItem, ResearchItemCarouselItem, ResearchItemCreator, ResearchInnovationPageCurrentResearch
from django.utils.dateparse import parse_date
from django.core.files import File
from importer.import_utils import richtext_from_elem, text_from_elem, make_slug, check_length
from importer import constants
import datetime
import urllib2
from bs4 import BeautifulSoup


# Interesting pages are pages that map onto fields in the staff page model
interesting_pages = {
    "Publications, Exhibitions & Other Outcomes": "publications_exhibtions_and_other_outcomes_placeholder",
    "Publication, Exhibitions & Other Outcomes": "publications_exhibtions_and_other_outcomes_placeholder",
    "Publications, Exhibitions and Other Outcomes": "publications_exhibtions_and_other_outcomes_placeholder",
    "Publications/Exhibitions/Other outcomes": "publications_exhibtions_and_other_outcomes_placeholder",
    "Publications and Exhibitions": "publications_exhibtions_and_other_outcomes_placeholder",
    "Publications & Exhibitions": "publications_exhibtions_and_other_outcomes_placeholder",
    "Exhibitions & Other Outcomes": "publications_exhibtions_and_other_outcomes_placeholder",
    "Publications & Other Outcomes": "publications_exhibtions_and_other_outcomes_placeholder",
    "Publications": "publications_exhibtions_and_other_outcomes_placeholder",

    "External Collaborations": "external_collaborations_placeholder",
    "External Collaborationns": "external_collaborations_placeholder",

    "Practice": "practice",

    "Research": "research_interests",

    "Current and Recent Projects": "current_recent_research",
    "Current and Recent Research Projects": "current_recent_research",

    "Awards/Grants": "awards_and_grants",
}


PATH = 'importer/data/export_staff_profiles.xml'
IMAGE_PATH = 'importer/data/export_staff_images/'
STAFF_INDEX_PAGE = StaffIndex.objects.get(slug='staff')
RESEARCH_INDEX_PAGE = CurrentResearchPage.objects.get(slug='current-research')


def cleanup_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove HR tags
    for hr in soup.find_all("hr"):
        hr.decompose()

    return unicode(soup)


def import_texts(element):
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


def import_image(element):
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

    # Load image file
    if not image.id:
        try:
            with File(open(IMAGE_PATH + image_filename.encode('utf-8'), 'r')) as f:
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


def import_staff_researchpage(staffpage, element):
    errors = {}

    # Get page info
    page_contentid = element.attrib['contentid']
    page_title, errors['title'] = text_from_elem(element, 'title', length=255, textify=True)
    page_texts, errors['texts'] = import_texts(element.find('texts'))

    # Check if this is an interesting page
    if page_title in interesting_pages:
        # Set the field for this page
        setattr(staffpage, interesting_pages[page_title], page_texts)

        # Get carousel images
        images_element = element.find('images')
        if images_element is not None:
            for image in images_element.findall('image'):
                # Import the image
                theimage, error = import_image(image)

                # Add to carousel
                if theimage is not None:
                    StaffPageCarouselItem.objects.get_or_create(page=staffpage, image=theimage)

    else:
        # Get school and programme from staffpage role
        try:
            staffpagerole = StaffPageRole.objects.get(page=staffpage)
            school = staffpagerole.school
            programme = staffpagerole.programme
        except StaffPageRole.DoesNotExist:
            school = ""
            programme = ""

        # Create research item
        try:
            researchitem = ResearchItem.objects.get(rca_content_id=page_contentid)
        except ResearchItem.DoesNotExist:
            researchitem = ResearchItem()
            researchitem.rca_content_id = page_contentid
        researchitem.title = page_title
        researchitem.research_type = "staff"
        researchitem.description = page_texts
        researchitem.school = school
        researchitem.programme = programme
        researchitem.slug = make_slug(researchitem)

        if researchitem.id:
            researchitem.save()
        else:
            RESEARCH_INDEX_PAGE.add_child(researchitem)

        # Link to creator
        ResearchItemCreator.objects.get_or_create(page=researchitem, person=staffpage)

        # Get carousel images
        images_element = element.find('images')
        if images_element is not None:
            for image in images_element.findall('image'):
                # Import the image
                theimage, error = import_image(image)

                # Add to carousel
                if theimage is not None:
                    ResearchItemCarouselItem.objects.get_or_create(page=researchitem, image=theimage)

    return errors


def import_staff(element):
    errors = {}

    # Basic info
    staff_contentid = element.attrib['contentid']
    staff_title, errors['title'] = text_from_elem(element, 'title', length=255, textify=True)
    staff_name, errors['name'] = text_from_elem(element, 'staffname', length=255, textify=True)
    staff_programme, errors['programme'] = text_from_elem(element, 'programme', length=255, textify=True)
    staff_statement, errors['statement'] = text_from_elem(element, 'statement')
    staff_biography, errors['biography'] = text_from_elem(element, 'biography')
    staff_school, errors['school'] = text_from_elem(element, 'school', length=255, textify=True)
    staff_editorialreference, errors['editorialreference'] = text_from_elem(element, 'editorialreference', length=255, textify=True)

    # Emails
    emails_element = element.find('emails')
    if emails_element is not None:
        staff_emails = [email.text for email in emails_element.findall('email')]
    else:
        staff_emails = []

    # URLs
    urls_element = element.find('urls')
    if urls_element is not None:
        staff_urls = [url.text for url in urls_element.findall('url')]
    else:
        staff_urls = []

    # Supervised students
    staff_supervisedstudents = []
    supervisedstudents_element = element.find('supervisedstudents')
    if supervisedstudents_element is not None:
        for supervisedstudent in supervisedstudents_element.findall('supervisedstudent'):
            supervised_student = supervisedstudent.text
            if supervised_student is not None:
                staff_supervisedstudents.append(supervisedstudent.text)



    # Cleanup statement and biography
    staff_statement = cleanup_html(staff_statement)
    staff_biography = cleanup_html(staff_biography)

    # Split name into first name, last name and title
    # A L Rees needs to be split up manually
    if staff_name == "A L Rees":
        staff_titleprefix = ""
        staff_firstname = "A L"
        staff_lastname = "Rees"
    else:
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
        staff_programme_split = staff_programme.split()
        if staff_programme_split[-1] == "Programme" or staff_programme_split[-1] == "Programmes":
            staff_programme = " ".join(staff_programme_split[:-1])

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
    staffpage.staff_type = "academic"
    staffpage.intro = staff_statement
    staffpage.biography = staff_biography
    staffpage.show_on_homepage = False
    staffpage.show_on_programme_page = False
    staffpage.title_prefix = staff_titleprefix
    staffpage.first_name = staff_firstname
    staffpage.last_name = staff_lastname
    if len(staff_supervisedstudents) > 0:
        staffpage.supervised_student_other = ", ".join(staff_supervisedstudents)
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
    if len(staff_emails) > 0:
        staffpagerole.email = staff_emails[0]
    staffpagerole.save()



    # Images
    images_element = element.find('images')
    if images_element is not None:
        for image in images_element.findall('image'):
            # Import the image
            theimage, error = import_image(image)

            # Add to carousel
            if theimage is not None:
                StaffPageCarouselItem.objects.get_or_create(page=staffpage, image=theimage)



    # Research pages
    researchpages_element = element.find('researchpages')
    if researchpages_element is not None:
        for researchpage in researchpages_element.findall('page'):
            import_staff_researchpage(staffpage, researchpage)

        # Research child pages
        research_childpages_element = researchpages_element.find('childpages')
        if research_childpages_element is not None:
            for childpage in research_childpages_element.findall('page'):
                import_staff_researchpage(staffpage, childpage)



    # Append URLs to bottom of practise block
    urls_html = "<ul>"
    for url in staff_urls:
        url_valid = url
        if "://" not in url_valid:
            url_valid = "http://" + url_valid
        urls_html += "<li><a href=\"" + url_valid + "\">" + url + "</a></li>"
    urls_html += "</ul>"
    staffpage.practice += urls_html



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
    root = ET.parse(PATH).getroot()

    # Departments
    for department in root.findall('department'):
        import_department(department)
