#import xml.etree.ElementTree as ET
from lxml import etree as ET
from rca.models import (
        StandardIndex,
        ProgrammePage,
        StudentPage,
        StudentPageContactsEmail,
        StudentPageContactsPhone,
        StudentPageContactsWebsite,
        StudentPageDegree,
        StudentPageAwards,
        StudentPageExperience,
        StudentPageExhibition,
        StudentPageCarouselItem,
        RcaImage,
        )
import markdown
import html2text
from django.utils.dateparse import parse_date
from django.utils.text import slugify
from django.core.files import File
import datetime
import urllib2
from importer.import_utils import richtext_from_elem, text_from_elem, make_slug, check_length
from importer.constants import DEGREE_SUBJECTS, SCHOOLS, PROGRAMMES

#NEWSINDEX = NewsIndex.objects.all()[0]
PATH = 'importer/export_2012_2_pretty.xml'
IMAGE_PATH = 'importer/show_2012_images/'
MASTERINDEX = StandardIndex.objects.get(slug='masterindex')
YEARS = [
        '2013',
        '2012',
        '2011',
        '2010',
        '2009',
        '2008',
        '2007',
        ]

def cv_handle(parent, elemname, model, page, **kwargs):
    length = kwargs.get('length', False)
    fieldname = kwargs.get('fieldname', elemname)

    elem = parent.find('elemname')
    objects = []
    errors = []
    if elem and elem.text:
        h = html2text.HTML2Text()
        h.body_width = 0
        for entry in h.handle(elem.text).split(';'):
            text = entry.strip()
            if length:
                text, error = check_length(text, length)
            obj = model()
            setattr(obj, fieldname, text)
            obj.page = page
            obj.save()
            errors.append(error)
    return errors



def doimport(path=PATH):
    tree = ET.parse(path)
    root = tree.getroot()
    errors = []
    images_errors = []
    for d in root.findall('department'):
        page = d.find('page')
        pageerrors = {}
        dept_title, pageerrors['title'] = text_from_elem(page, 'title')
        print '\n' + thepage.title
        try:
            thepage = show_index.get_children().get(title=title)
        except DoesNotExist:
            thepage = ProgrammePage(title=title)
        theprogramme = PROGRAMMES[thepage.title]
        print theprogramme
        theschool = SCHOOLS[thepage.title]
        print theschool

        print thepage.body
        # save the page
        MASTERINDEX.add_child(thepage)

        for s in d.findall('student'):
            s = s.find('studentpage')
            sp = StudentPage()
            sp_errs = {}

            sp.title, sp_errs['title'] = text_from_elem(s, 'title', length=255)
            # there is no intro text in any of the data at time of writing
            # intro, sp_errs['intro'] = text_from_elem(s, 'intro')
            sp.slug = make_slug(sp)
            #sp.statement, sp_errs['statement'] = text_from_elem(s, 'statement', length=255)
            # TODO we may need more detailed parsing of the following
            # paragraph, to search for 'supported by' and 'collaboration' or
            # some such, and get them out into a separate field
            sp.statement = richtext_from_elem(s.find('statement'))


            # handle the metadata fields
            metadata = s.find('metadata')
            # format the current degree
            sp.degree_year, sp_errs['deg_year'] = text_from_elem(metadata, 'year', length=255)
            degree_subject, sp_errs['deg_subj'] = text_from_elem(metadata, 'degrees', length=255)
            if degree_subject[-1] == '?':
                degree_subject = degree_subject[:-1]
            sp.degree_subject = DEGREE_SUBJECTS[degree_subject]
            degree_qualification, sp_errs['deg_qual'] = text_from_elem(metadata, 'degree', length=255)
            sp.degree_qualification = degree_qualification

            sp.programme = thepage.programme
            sp.school = thepage.school
            if s.find('specialism') is not None:
                sp.specialism, sp_errs['specialism'] = text_from_elem(metadata, 'specialism')
            
            # no profile images yet, use a nice one
            sp.profile_image = RcaImage.objects.get(id=6)


            # save the studentpage for foreignkey purposes
            thepage.add_child(sp)

            # handle the cv fields
            cv = s.find('cv')

            sp_errs['degree'] = cv_handle(
                    cv, 'degree', StudentPageDegree, sp, length=255, fieldname='degree')
            sp_errs['exhibition'] = cv_handle(
                    cv, 'exhibition', StudentPageExhibition, sp, length=255)
            sp_errs['awards'] = cv_handle(
                    cv, 'awards', StudentPageAwards, sp, length=255, fieldname='award')
            sp_errs['experience'] = cv_handle(
                    cv, 'experience', StudentPageExperience, sp, length=255)
            # currently the model doesn't have publications or conferences
            #sp_errs['publications'] = cv_handle(
            #        cv, 'publications', StudentPagePublications, sp, length=255)
            #sp_errs['conferences'] = cv_handle(
            #        cv, 'conferences', StudentPageConferences, sp, length=255)
            
            if s.find('emails') is not None:
                for emailaddress in s.find('emails').getchildren():
                    emailpage = StudentPageContactsEmail(page = sp)
                    emailpage.email = emailaddress.text.strip()
                    try:
                        emailpage.save()
                    except Exception, e:
                        sp_errs['email ' + emailaddress.text.strip()] = e.message

            if s.find('urls') is not None:
                for url in s.find('urls').getchildren():
                    websitepage = StudentPageContactsWebsite(page = sp)
                    websitepage.email = url.text.strip()
                    try:
                        websitepage.save()
                    except Exception, e:
                        sp_errs['website ' + url.text.strip()] = e.message

            if s.find('phonenumbers') is not None:
                for num in s.find('phonenumbers').getchildren():
                    phonepage = StudentPageContactsPhone(page = sp)
                    phonepage.email = num.text.strip()
                    try:
                        phonepage.save()
                    except Exception, e:
                        sp_errs['phone ' + num.text.strip()] = e.message

            # handle images tag
            images = s.find('images')
            if images:
                for image in images.findall('image'):
                    imageerrors = {}
                    metadata = image.find('imagemetadata')
                    newimage = RcaImage()
                    newimage.title, imageerrors['title'] = text_from_elem(metadata, 'title', length=255)
                    newimage.creator, imageerrors['creator'] = text_from_elem(metadata, 'creator', length=255)
                    newimage.medium, imageerrors['medium'] = text_from_elem(metadata, 'media', length=255)
                    newimage.photographer, imageerrors['photographer'] = text_from_elem(metadata, 'photographer', length=255)
                    newimage.permissions, imageerrors['permissions'] = text_from_elem(metadata, 'rights', length=255)

                    caption, imageerrors['caption'] = text_from_elem(metadata, 'caption', length=255, textify=True)
                    newimage.alt = caption
                    

                    #newimage.width, imageerrors['width'] = text_from_elem(metadata, 'width', length=255)
                    #newimage.height, imageerrors['height'] = text_from_elem(metadata, 'height', length=255)

                    filename = urllib2.unquote(image.find('filename').text.strip())
                    with File(open(IMAGE_PATH + filename, 'r')) as f:
                        newimage.file = f
                        newimage.save()

                    carousel = StudentPageCarouselItem(
                            page = sp,
                            image = newimage,
                            overlay_text = caption,
                            )
                    carousel.save()

                    imageerrordict = dict((k, v) for k, v in imageerrors.iteritems() if v)
                    if imageerrordict:
                        images_errors.append({image: imageerrordict})

        errordict = dict((k, v) for k, v in pageerrors.iteritems() if v)
        if errordict:
            errors.append({dept_title: errordict})
    return images_errors, errors
