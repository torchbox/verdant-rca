from rca.models import ResearchItem
import os
import httplib2
import json
from collections import namedtuple
import csv
import re


class ResearchBookTitlesImporter(object):
    def __init__(self, **kwargs):
        self.save = kwargs.get('save', False)
        self.research_csv_filename = kwargs.get('research_csv_filename', 'importer/data/research.csv')
        self.cache_directory = kwargs.get('cache_directory', 'importer/data/research/')
        self.http = httplib2.Http()

        # Create cache directories
        try:
            os.makedirs(self.cache_directory)
        except OSError: # Directory alredy exists
            pass

    def import_researchitem(self, element):
        # Get basic info
        researchitem_eprintid = element['eprintid']
        researchitem_type = element['type']

        # Check that this is a book_section
        if researchitem_type != 'book_section':
            return

        # Find research item record
        try:
            researchitem = ResearchItem.objects.get(eprintid=researchitem_eprintid)
        except ResearchItem.DoesNotExist:
            print "Cannot find research item. Eprintid: " + str(researchitem_eprintid)
            return

        # Add book title
        researchitem.subtitle = element['book_title']

        # Save
        if self.save:
            researchitem.save()

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

    def run(self):
        # Load research
        ResearchRecord = namedtuple('ResearchRecord', 'author, output_type, title, ref_url')
        research_csv = csv.reader(open(self.research_csv_filename, 'rb'))

        # Expression for finding eprintids in ref urls
        eprint_expr = re.compile(r'^(?:http|https)://researchonline.rca.ac.uk/(\d+)/')

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


def run(save=False):
    # Import
    importer = ResearchBookTitlesImporter(save=save)
    importer.run()
