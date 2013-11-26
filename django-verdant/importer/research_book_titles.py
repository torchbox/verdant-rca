from rca.models import ResearchItem
import os
import httplib2
import json


class ResearchBookTitlesImporter(object):
    def __init__(self, **kwargs):
        self.save = kwargs.get('save', False)
        self.cache_directory = kwargs.get('cache_directory', 'importer/data/research/')
        self.http = httplib2.Http()

        # Create cache directories
        try:
            os.makedirs(self.cache_directory)
        except OSError: # Directory alredy exists
            pass

    def import_researchitem(self, element):
        # Get basic info
        eprintid = element['eprintid']

        # Check that this is a book_section
        if element['type'] != 'book_section':
            return

        # Find research item record
        try:
            researchitem = ResearchItem.objects.get(eprintid=eprintid)
        except ResearchItem.DoesNotExist:
            print "Cannot find research item. Eprintid: " + str(eprintid)
            return

        # Add book title
        researchitem.subtitle = element['book_title']

        # Save
        if self.save:
            researchitem.save()

        # Find latest revision of researchitem
        researchitem_latest_revision = researchitem.get_latest_revision_as_page()

        # Add book title to latest revision
        researchitem_latest_revision.subtitle = element['book_title']

        # Save latest revision
        if self.save:
            researchitem_latest_revision.save_revision()

    def get_research_file(self, eprintid):
        # Attempt to load from cache
        filename = self.cache_directory + eprintid + '.json'
        try:
            return open(filename, 'r')
        except IOError:
            pass

        # Download instaed
        url = 'http://researchonline.rca.ac.uk/cgi/export/eprint/%(eprintid)s/JSON/rca-eprint-%(eprintid)s.js' % {
            'eprintid': eprintid,
        }
        status, response = self.http.request(url)
        if status['status'] == '200':
            # Save file to disk
            f = open(filename, 'w')
            f.write(response)
            f.close()

            # Return new handle to file
            return open(filename, 'r')
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

    def run(self, eprintid_list):
        # Loop through eprint ids
        for eprintid in eprintid_list:
            self.import_researchitem_from_eprintid(str(eprintid))


def run(save=False, eprints_file='importer/data/research_eprints.json'):
    # Load json file
    with open(eprints_file, 'r') as f:
        eprintid_list = json.load(f)

    # Import
    importer = ResearchBookTitlesImporter(save=save)
    importer.run(eprintid_list)
