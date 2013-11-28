from verdant.verdantcore.models import Page
from rca.models import ResearchItem
import csv


THEMES_MAPPING = {
    'Cultures of Curating': 'culturesofcurating',
    'Design, Innovation and Society': 'designinnovationandsociety',
    'Dialogues of Form and Surface': 'dialoguesofformandsurface',
    'Image and Language': 'imageandlanguage',
}


class ThemeImporter(object):
    def __init__(self, save=False, staff_index='staff', student_index='research-students'):
        self.save = save

        # Get index pages
        self.staff_index_page = Page.objects.get(slug=staff_index)
        self.student_index_page = Page.objects.get(slug=student_index)

    def find_person_page(self, person_name):
        # Get list of potential names
        names = [title + ' ' + person_name for title in ['Dr', 'Professor', 'Sir']]
        names.append(person_name)

        # Slugify them
        slugs = map(lambda slug: slug.strip(' ').replace("'", '').lower().replace(' ', '-'), names)

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

    def import_themes(self, person_themes):
        # Loop through person-themes list
        for person_theme in person_themes:
            # Find theme name
            if person_theme[1] in THEMES_MAPPING:
                theme = THEMES_MAPPING[person_theme[1]]
            else:
                print 'Error: Unrecognised theme "' + person_theme[1] + '"'
                continue

            # Find person
            person_page = self.find_person_page(person_theme[0])
            if person_page is None:
                print 'Error: Could not find profile page for "' + person_theme[0] + '"'
                continue

            # Find all research items for this person
            research_items = ResearchItem.objects.filter(creator__person=person_page)
            for research_item in research_items:
                # Set the theme
                research_item.theme = theme

                # Save it
                if self.save:
                    research_item.save()


def run(save=False):
    # Create theme importer object
    importer = ThemeImporter(save)

    # Get list of person-themes
    with open('importer/data/staff_themes.csv', 'r') as f:
        person_themes = [row for row in csv.reader(f)]

    # Run importer
    importer.import_themes(person_themes)