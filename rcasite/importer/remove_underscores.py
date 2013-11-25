from rca.models import RcaImage
import re


SUB_EXPRESSIONS = (
    # Removes HTML tags
    (r'<.*?>', ''),

    # Removes \r\n
    (r'\\r\\n', ' '),

    # Unescapes double quotes
    (r'\\"', '"'),

    # Removes underscores at beginning of words
    (r' _', ' '),
    (r'^_', ''),

    # Removes underscores at end of words
    (r'_ ', ' '),
    (r'_$', ''),

    # Removes underscores before certian punctuation marks
    (r'_,', ','),    # Comma
    (r'_\'', '\''),  # Single quote
    (r'_\)', ')'),   # Close bracket

    # Removes underscores after certian punctuation marks
    (r'\'_', '\''),  # Single quote
)


class UnderscoresRemover(object):
    def __init__(self, save=False):
        self.save = save

        # Compile sub expressions
        self.sub_expressions_compiled = [(re.compile(sub_expr[0]), sub_expr[1]) for sub_expr in SUB_EXPRESSIONS]

    def clean_text(self, text):
        # Run sub expressions on string
        for sub_expr in self.sub_expressions_compiled:
            text = sub_expr[0].sub(sub_expr[1], text)

        return text

    def clean_images(self):
        # Loop through images
        for image in RcaImage.objects.all():
            # Clean text fields in image
            image.title = self.clean_text(image.title)
            image.alt = self.clean_text(image.alt)

            # Save image
            if self.save:
                image.save()


def run(save=False):
    # Create remover object
    remover = UnderscoresRemover(save)

    # Clean images
    print 'Cleaning images...'
    remover.clean_images()

    # Print done
    print 'done'