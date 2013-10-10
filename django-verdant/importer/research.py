import httplib2
import json
import markdown
from rca.models import ResearchItem, ResearchItemCarouselItem, ResearchItemCreator, ResearchItemLink, Page, RcaImage
from importer.staffdata import staff_data
from django.utils.dateparse import parse_date
from django.core.files.base import ContentFile
from django.core.files import File
from importer.import_utils import check_length, make_slug, mdclean
from importer.constants import SCHOOLS

http = httplib2.Http()

STAFF_INDEX_PAGE = Page.objects.get(slug='staff-index-page')
RESEARCH_INDEX_PAGE = Page.objects.get(slug='current-research')
STAFF_LIST = staff_data[0:]
EXPORT_PATH = 'importer/research_export.json'

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
work_types = set()
file_types = {}
weird = []

VIDEO_TYPES = [
    'video/mp4',
    'video/ogg',
    'video/quicktime',
    ]
AUDIO_TYPES = [
    'audio/ogg',
    'audio/mp4',
    ]
IMAGE_TYPES = [
    'image/png',
    'image/jpeg',
    'image/gif',
    'image/jpg',
    ]
TEXT_TYPES = [
    'text/plain',
    ]
PROGRAM_TYPES = [
    'text/x-pl1',
    'text/x-java',
    'text/x-c',
    'text/x-c++',
    ]
DOC_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'application/x-zip',
    'text/html',
    ]
UNHANDLED_TYPES = [
    'application/octet-stream',
    'image/tiff',
    ]



def downloadexport(**kwargs):
    staff_list = kwargs.get('staff_list', STAFF_LIST)
    export_path = kwargs.get('export_path', EXPORT_PATH)
    f = open(export_path, 'w')
    for entry in staff_list:
        username = entry['sAMAccountName']
        url = 'http://researchonline.rca.ac.uk/cgi/search/archive/simple/export_rca_JSON.js?screen=Search&dataset=archive&_action_export=1&output=JSON&exp=0%%7C1%%7C%%7Carchive%%7C-%%7Cq%%3A%%3AALL%%3AIN%%3A%(username)s%%7C-%%7C&n=&cache=' % {
            'username': username,
            }
        print username
        status, response = http.request(url)
        if status['status'] == '200':
            f.write(response)
        print len(response)
    f.close()


def doimport(**kwargs):
    staff_list = kwargs.get('staff_list', STAFF_LIST)
    staff_index_page = kwargs.get('staff_index_page', STAFF_INDEX_PAGE)
    research_index_page = kwargs.get('research_index_page', RESEARCH_INDEX_PAGE)
    start_at = kwargs.get('start_at', 0)


    hasitemscount = 0
    hasdocscount = 0
    interestingdocscount = 0
    totalfilescount = 0

    for index, entry in enumerate(staff_list):
        if index < start_at:
            continue
        username = entry['sAMAccountName']
        url = 'http://researchonline.rca.ac.uk/cgi/search/archive/simple/export_rca_JSON.js?screen=Search&dataset=archive&_action_export=1&output=JSON&exp=0%%7C1%%7C%%7Carchive%%7C-%%7Cq%%3A%%3AALL%%3AIN%%3A%(username)s%%7C-%%7C&n=&cache=' % {
            'username': username,
            }
        status, response = http.request(url)
        print '\n#' + str(index) + ' - ' + username + ': ' + status['status']
        if status['status'] == '200':
            researchitems = json.loads(response)
            if len(researchitems) > 0:
                hasitemscount += 1
            usererrors = []
            itemcount = 0
            savecount = 0
            docsavecount = 0
            interestingcount = 0
            filesavecount = 0
            for item in researchitems:
                itemcount += 1
                itemerrors = {}
                save = True
                #save = False
                eprintid = item['eprintid']
                title = item['title']
                try:
                    ri = ResearchItem.objects.get(eprintid=eprintid)
                    if ri.title != title:
                        usererrors.append((eprintid,title,'mismatch'))
                        save = False
                except ResearchItem.DoesNotExist:
                    ri = ResearchItem(eprintid=eprintid)
                ri.title, itemerrors['title'] = check_length(title, 255)
                ri.slug = make_slug(ri)
                date = item.get('date', None)
                if date:
                    if isinstance(date, basestring):
                        try:
                            ri.year = str(parse_date(date).year)
                        except AttributeError:
                            ri.year = date[0:4]
                    elif isinstance(date, int):
                        ri.year = str(date)
                abstract = item.get('abstract', '')
                ri.description = markdown.markdown(mdclean(abstract))
                work_type = item['type']
                work_types.add(work_type)
                ri.work_type = WORK_TYPES_CHOICES[work_type]
                department = item.get('department', '')
                while department:
                    try:
                        ri.school = SCHOOLS[department]
                        break
                    except KeyError:
                        simpletitle = str(ri.title.encode('utf-8').decode('ascii', 'ignore'))
                        department = raw_input(u"Eprint id: %s\nResearch item: %s\nClaimed programme: %s\n\nPlease type the real name of the programme or leave blank:\n" % (eprintid, simpletitle, department))
                if save:
                    if ri.id:
                        ri.save()
                    else:
                        research_index_page.add_child(ri)
                    savecount += 1

                # handle documents
                if 'documents' not in item.keys():
                    print 'Research item ' + str(itemcount)
                    print 'No docs'
                else:
                    hasdocscount += 1
                    print 'Research item ' + str(itemcount)
                    print str(len(item['documents'])) + ' docs'
                    for d in item['documents']:
                        # we're not interested in password-protected files
                        if d['security'] == 'staffonly':
                            continue
                        # equally we're not interested in thumbnails etc.
                        if 'relation' in d.keys():
                            if 'isVersionOf' in d['relation'][0]['type']:
                                continue

                        if 'files' in d.keys():
                            if len(d['files']) != 1:
                                weird.append(docid)
                            for f in d['files']:
                                uri = f['uri']
                        # get the file_types
                        try:
                            file_type = d['mime_type']
                        except KeyError:
                            itemerrors['file'] = 'no mime_type'
                            continue
                        current_total = file_types.get(file_type, 0)
                        file_types[file_type] = current_total + 1
                        interestingcount += 1

                        docid = str(d['docid'])
                        if file_type in IMAGE_TYPES:
                            try:
                                image = RcaImage.objects.get(eprint_docid = docid)
                            except RcaImage.DoesNotExist:
                                image = RcaImage(eprint_docid = docid)

                            print uri
                            response, content = http.request(uri)
                            if response['status'] == '200':
                                with open('importer/temp', 'w') as f:
                                    f.write(content)
                                with File(open('importer/temp', 'r')) as f:
                                    image.file = f
                                    image.save()
                                    filesavecount += 1

                                if ResearchItemCarouselItem.objects.filter(page=ri,image=image).count() == 0:
                                    carousel = ResearchItemCarouselItem(
                                            page = ri,
                                            image = image,
                                            )
                                    carousel.save()
                            else:
                                itemerrors['file'] = 'bad http response'
                                continue
                    print str(interestingcount) + ' turned out to be interesting'

                totalfilescount += filesavecount
                interestingdocscount += interestingcount

        if itemcount:
            print "%(items)s research items, %(saved)s saved, %(docs)s docs, %(interesting)s interesting, %(files)s files saved" % {
                    'items': str(itemcount),
                    'interesting': str(interestingcount),
                    'saved': str(savecount),
                    'docs': str(docsavecount),
                    'files': str(filesavecount),
                    }
        else:
            print "No research items"
    print "Research import finished.\n%(people)s people looked at.\n%(items)s had research items, \n%(docs)s of which had docs; \n%(interesting)s interesting docs\n%(files)s files actually saved" % {
            'people': str(len(staff_list)),
            'items': str(hasitemscount),
            'docs': str(hasdocscount),
            'interesting': str(interestingdocscount),
            'files': str(totalfilescount),
            }
