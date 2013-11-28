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
        StudentPageWorkCollaborator,
        StudentPageWorkSponsor,
        RcaImage,
        )
from verdant.verdantcore.models import (
        Page,
        )
import markdown
import html2text
from django.utils.dateparse import parse_date
from django.utils.text import slugify
from django.core.files import File
import datetime
import urllib2
from unicodedata import normalize
from importer.import_utils import (
        richtext_from_elem,
        text_from_elem,
        make_slug,
        check_length,
        statement_extract,
        )
from importer.constants import DEGREE_SUBJECTS, SCHOOLS, PROGRAMMES, PROGRAMME_SPECIALISMS
from bs4 import BeautifulSoup

PATH = 'importer/data/export_2013.xml'
IMAGE_PATH = 'importer/data/show_images/'
try:
    SHOW_INDEX = StandardIndex.objects.get(slug='show-rca')
except StandardIndex.DoesNotExist:
    print "Create an index page with slug 'show-rca'"
    raise
# try:
#     PLACEHOLDER_IMAGE = RcaImage.objects.get(rca_content_id='placeholder')
# except RcaImage.DoesNotExist:
#     newimage = RcaImage(title='placeholder',rca_content_id='placeholder')
#     while not newimage.id:
#         image_path = raw_input(u"Placeholder image not found.\nEnter the path of an image to use as placeholder:\n")
#         with File(open(image_path, 'r')) as f:
#             newimage.file = f
#             newimage.save()
#     PLACEHOLDER_IMAGE = newimage

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
    save = kwargs.get('save', False)
    fieldname = kwargs.get('fieldname', elemname)

    elem = parent.find(elemname)
    objects = []
    errors = []
    if elem is not None and elem.text is not None:
        # first clear all existing ones
        if save:
            model.objects.filter(page=page).delete()

        for entry in BeautifulSoup(elem.text, 'html.parser').text.split(';'):
            text = entry.strip()
            if length:
                text, error = check_length(text, length)
            obj = model()
            setattr(obj, fieldname, text)
            obj.page = page
            if save:
                obj.save()
            if error:
                errors.append(error)
    return errors


def clear_students(**kwargs):
    year = kwargs.get('year', None)
    if year:
        student_pages = StudentPage.objects.filter(degree_year=year)
    else:
        student_pages = StudentPage.objects.all()
    count = student_pages.count()
    print str(count) + ' to delete'
    carousels = StudentPageCarouselItem.objects.filter(page__in = student_pages)
    print str(carousels.count()) + ' related images'
    for s in student_pages:
        for c in StudentPageCarouselItem.objects.filter(page=s):
            c.image.delete()
        print 'deleting ' + str(s.id)
        Page.objects.get(id=s.id).delete()

    print str(count) + ' deleted'


def doimport(**kwargs):
    save = kwargs.get('save', False)
    path = kwargs.get('path', PATH)
    image_path = kwargs.get('image_path', IMAGE_PATH)
    show_index = SHOW_INDEX
    tree = ET.parse(path)
    root = tree.getroot()
    errors = {}
    images_errors = []
    dept_count = 0
    total_students = 0
    new_count = 0
    student_save_count = 0
    for d in root.findall('department'):
        dept_count += 1
        page = d.find('page')
        depterrors = {}
        dept_title, depterrors['title'] = text_from_elem(page, 'title')
        specialism = ''
        print '\nNow importing: ' + repr(dept_title)
        if dept_title in PROGRAMME_SPECIALISMS.keys():
            dept_title, specialism = PROGRAMME_SPECIALISMS[dept_title]
        print 'dept: ' + repr(dept_title)
        theprogramme = PROGRAMMES[dept_title]
        print 'prog: ' + repr(theprogramme)
        theschool = SCHOOLS[dept_title]
        print 'scho: ' + repr(theschool)

        h = html2text.HTML2Text()
        h.body_width = 0
        try:
            blurb = page.find('texts').findall('text')[0].find('content')
        except AttributeError:
            blurb = page.find('synopsis')
        blurb = h.handle(blurb.text).strip()
        print "Blurb: " + repr(blurb)
        print "******* note that the above text will not be imported *******"

        student_count = 0

        for s in d.findall('student'):
            student_count += 1
            s = s.find('studentpage')
            sp_contentid = s.attrib['contentid']
            try:
                sp = StudentPage.objects.get(rca_content_id=sp_contentid)
            except StudentPage.DoesNotExist:
                sp = StudentPage(rca_content_id=sp_contentid)
            sp_errs = {}

            sp.title, sp_errs['title'] = text_from_elem(s, 'title', length=255)
            # there is no intro text in any of the data at time of writing
            # intro, sp_errs['intro'] = text_from_elem(s, 'intro')
            sp.slug = make_slug(sp)
            statement = richtext_from_elem(s.find('statement'))

            statement_text, sponsors, collaborators = statement_extract(statement)
            sp.statement = statement_text
            sp.work_description = statement_text

            # handle the metadata fields
            metadata = s.find('metadata')
            # format the current degree
            sp.degree_year, sp_errs['deg_year'] = text_from_elem(metadata, 'year', length=255)
            degree_subject, sp_errs['deg_subj'] = text_from_elem(metadata, 'degrees', length=255)
            if degree_subject[-1] == '?':
                degree_subject = degree_subject[:-1]
            sp.degree_subject = DEGREE_SUBJECTS[degree_subject]
            degree_qualification, sp_errs['deg_qual'] = text_from_elem(metadata, 'degree', length=255)
            sp.degree_qualification = degree_qualification.lower()
            # metadata contains first and last names in separate fields
            sp.first_name, sp_errs['first_name'] = text_from_elem(metadata, 'firstname', length=255)
            sp.last_name, sp_errs['last_name'] = text_from_elem(metadata, 'surname', length=255)
            # we worked out the programme and school earlier from the dept_page
            sp.programme = theprogramme
            sp.school = theschool
            if not specialism and metadata.find('specialism') is not None:
                sp.specialism, sp_errs['specialism'] = text_from_elem(metadata, 'specialism')
            else:
                sp.specialism = specialism
            # handle profile image
            try:
                profile_image = RcaImage.objects.get(rca_content_id=sp_contentid + 'profile_image')
            except RcaImage.DoesNotExist:
                profile_image = RcaImage(rca_content_id=sp_contentid + 'profile_image')
            profile_filename = slugify(unicode(sp.title)).replace('-','_')
            profile_image_path = image_path + "show_2013_profiles/2400_" + sp.programme + "/"
            profile_image.title = sp.title + ' profile image'
            if not profile_image.id:
                try:
                    with File(open(normalize("NFKD", profile_image_path + profile_filename + '.jpg'), 'rb')) as f:
                        profile_image.file = f
                        if save:
                            profile_image.save()
                except IOError as e:
                    try:
                        with File(open(normalize("NFKD", profile_image_path + profile_filename + '.png'), 'rb')) as f:
                            profile_image.file = f
                            if save:
                                profile_image.save()
                    except IOError as e:
                        print "I/O error({0}): {1}".format(e.errno, e.strerror) + " " + profile_image_path + profile_filename
                        sp_errs['image_not_found'] = profile_image_path + profile_filename
                except ValueError:
                    print "Could not convert data to an integer."
                except:
                    import sys
                    print "Unexpected error:", sys.exc_info()[0]
                    raise
            else:
                if save:
                    profile_image.save()
            sp.profile_image = profile_image

            # save the studentpage for foreignkey purposes
            if save:
                student_save_count += 1
                if sp.id:
                    sp.save()
                else:
                    new_count += 1
                    show_index.add_child(sp)
            elif not sp.id:
                new_count += 1

            # handle the sponsors and collaborators from earlier
            for spon in sponsors:
                name, sp_errs['sponsors'] = check_length(spon, 255)
                if save:
                    sponpage = StudentPageWorkSponsor(page=sp, name=name)
                    sponpage.save()
            for col in collaborators:
                name, sp_errs['collaborators'] = check_length(col, 255)
                if save:
                    colpage = StudentPageWorkCollaborator(page=sp, name=name)
                    colpage.save()

            # handle the cv fields
            cv = s.find('cv')

            sp_errs['degree'] = cv_handle(
                    cv, 'degrees', StudentPageDegree, sp, length=255, fieldname='degree', save=save)
            sp_errs['exhibition'] = cv_handle(
                    cv, 'exhibition', StudentPageExhibition, sp, length=255, save=save)
            sp_errs['experience'] = cv_handle(
                    cv, 'experience', StudentPageExperience, sp, length=255, save=save)
            sp_errs['awards'] = cv_handle(
                    cv, 'awards', StudentPageAwards, sp, length=255, fieldname='award', save=save)
            if cv.find('sponsors') is not None:
                sp_errs['sponsors'] = cv_handle(
                        cv, 'sponsors', StudentPageWorkSponsor, sp, length=255, fieldname='name', save=save)
            # currently the model doesn't have publications or conferences
            #sp_errs['publications'] = cv_handle(
            #        cv, 'publications', StudentPagePublications, sp, length=255)
            #sp_errs['conferences'] = cv_handle(
            #        cv, 'conferences', StudentPageConferences, sp, length=255)
            
            if s.find('emails') is not None:
                for emailaddress in s.find('emails').getchildren():
                    emailtext = emailaddress.text.strip()
                    if save:
                        StudentPageContactsEmail.objects.get_or_create(page=sp, email=emailtext)

            if s.find('phonenumbers') is not None:
                for num in s.find('phonenumbers').getchildren():
                    if num.text:
                        phonenumber = num.text.strip()
                        if save:
                            StudentPageContactsPhone.objects.get_or_create(page=sp, phone=phonenumber)

            if s.find('urls') is not None:
                for url in s.find('urls').getchildren():
                    if url.text:
                        urltext = url.text.strip()
                        if save:
                            StudentPageContactsWebsite.objects.get_or_create(page=sp, website=urltext)

            # handle images tag
            images = s.find('images')
            forloop_counter = 0
            if images is not None:
                for image in images.findall('image'):
                    forloop_counter += 1
                    imageerrors = {}
                    metadata = image.find('imagemetadata')
                    im_contentid = image.attrib['contentid']
                    if not im_contentid:
                        im_contentid = sp_contentid + '_image_' + str(forloop_counter)
                    try:
                        theimage = RcaImage.objects.get(rca_content_id=im_contentid)
                    except RcaImage.DoesNotExist:
                        theimage = RcaImage(rca_content_id=im_contentid)
                    theimage.title, imageerrors['title'] = text_from_elem(metadata, 'title', length=255, textify=True)
                    theimage.creator, imageerrors['creator'] = text_from_elem(metadata, 'creator', length=255, textify=True)
                    theimage.medium, imageerrors['medium'] = text_from_elem(metadata, 'media', length=255, textify=True)
                    photographer, imageerrors['photographer'] = text_from_elem(metadata, 'photographer', length=255)
                    if photographer.strip().startswith('&copy;'):
                        photographer = photographer.replace('&copy;', '').strip()
                    theimage.photographer = photographer
                    theimage.permissions, imageerrors['permissions'] = text_from_elem(metadata, 'rights', length=255)

                    caption, imageerrors['caption'] = text_from_elem(metadata, 'caption', length=255, textify=True)
                    theimage.alt = caption
                    

                    #theimage.width, imageerrors['width'] = text_from_elem(metadata, 'width', length=255)
                    #theimage.height, imageerrors['height'] = text_from_elem(metadata, 'height', length=255)

                    filename = unicode(urllib2.unquote(image.find('filename').text.strip()))
                    image_success = False
                    full_image_path = image_path + '2400_' + sp.programme + "/"
                    if not theimage.id:
                        try:
                            with File(open(normalize("NFKD", full_image_path + filename), 'rb')) as f:
                                theimage.file = f
                                if save:
                                    theimage.save()
                                    image_success = True
                        except IOError as e:
                            try:
                                with File(open(normalize("NFKD", full_image_path + filename[:-4] + '.png'), 'rb')) as f:
                                    theimage.file = f
                                    if save:
                                        theimage.save()
                                        image_success = True
                            except IOError as e:
                                print "I/O error({0}): {1}".format(e.errno, e.strerror)
                                print full_image_path + filename
                                imageerrors['image_not_found'] = full_image_path + filename
                        except ValueError:
                            print "Could not convert data to an integer."
                        except:
                            import sys
                            print "Unexpected error:", sys.exc_info()[0]
                            raise
                    else:
                        if save:
                            theimage.save()
                            image_success = True
                    if save and image_success:
                        StudentPageCarouselItem.objects.get_or_create(page=sp, image=theimage)

                    newimageerrordict = dict((k, v) for k, v in imageerrors.iteritems() if v)
                    if newimageerrordict:
                        images_errors.append({image: newimageerrordict})
            errordict = dict((k, v) for k, v in sp_errs.iteritems() if v)
            if errordict:
                depterrors[sp.title] = errordict
        errordict = dict((k, v) for k, v in depterrors.iteritems() if v)
        if errordict:
            errors[theprogramme] = errordict
        print "%(student_count)s students" % { 'student_count': student_count }
        total_students += student_count
    print "%(d)s departments imported, total %(s)s students, %(sv)s saved (%(n)s new)" % {
            'd': dept_count,
            's': total_students,
            'sv': student_save_count,
            'n': new_count,
            }
    profile_not_found_count = 0
    image_not_found_count = 0
    for dept, depterrors in errors.iteritems():
        print '\n' + dept + '\n' + '='*len(dept)
        for name, sp_errs in depterrors.iteritems():
            if isinstance(sp_errs, dict):
                print name
                print sp_errs['image_not_found']
                profile_not_found_count += 1
    print '\nImage errors\n============'
    for image_dict in images_errors:
        for image, error_dict in image_dict.iteritems():
            if isinstance(error_dict, dict):
                print error_dict['image_not_found']
                image_not_found_count += 1

    print str(profile_not_found_count) + " profile images not found"
    print str(image_not_found_count) + " artwork images not found"
    print '\n\n'
    return images_errors, errors
