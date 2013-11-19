from rca.models import StudentPage, StudentPagePublication, StudentPageConference
from lxml import etree as ET
import re


class Show2013ConfPubImporter(object):
    def __init__(self, save=False):
        self.save = save
        self.tag_expr = re.compile(r'<.*?>')

        self.student_count = 0
        self.publication_count = 0
        self.conference_count = 0

    def strip_tags(self, text):
        return self.tag_expr.sub('', text)

    def import_student(self, element):
        # Get content id
        contentid = element.attrib['contentid']

        # Find student page
        try:
            student_page = StudentPage.objects.get(rca_content_id=contentid)
        except StudentPage.DoesNotExist:
            print "WARN: Cannot find student page: " + contentid
            return

        # Increment student count
        self.student_count += 1

        # Get publications and conferences
        cv = element.find('cv')
        publications = cv.find('publications').text
        conferences = cv.find('conferences').text

        # Save publications
        if publications:
            publications_clean = self.strip_tags(publications)
            publications_list = publications_clean.split(';')
            for publication in publications_list:
                self.publication_count += 1
                publication_clean = publication.strip()
                if self.save:
                    StudentPagePublication.objects.get_or_create(page=student_page, name=publication_clean)

        # Save conferences
        if conferences:
            conferences_clean = self.strip_tags(conferences)
            conferences_list = conferences_clean.split(';')
            for conference in conferences_list:
                self.conference_count += 1
                conference_clean = conference.strip()
                if self.save:
                    StudentPageConference.objects.get_or_create(page=student_page, name=conference_clean)

    def import_department(self, element):
        for student in element.findall('student'):
            self.import_student(student.find('studentpage'))

    def run(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()

        # Import departments
        for department in root.findall('department'):
            self.import_department(department)


def run(save=False, filename='importer/data/export_2013.xml'):
    # Create a new importer
    importer = Show2013ConfPubImporter(save=save)

    # Run importer
    importer.run(filename)

    # Print stats
    print "Imported %d students, %d publictions and %d conferences" % (
        importer.student_count, importer.publication_count, importer.conference_count
    )