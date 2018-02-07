import re

from wagtailcaptcha.models import WagtailCaptchaFormBuilder


class EnquiryFormDOBMixin(object):
    """
    Convert date format from DD/MM/YYYY to YYYY-MM-DD before form
    is validated.
    """
    def __init__(self, data, *args, **kwargs):
        data = self.process_enquiry_form_request(data)

        super(EnquiryFormDOBMixin, self).__init__(data, *args, **kwargs)

        self.fields

    def process_enquiry_form_request(self, data):
        """
        Convert date of birth from DD/MM/YYYY format to YYYY-MM-DD
        only if format matched. Otherwise leave untouched.
        """

        date_of_birth = data.get('date-of-birth', None)

        if date_of_birth:
            date_of_birth = date_of_birth.strip()

            # Matches only DD/MM/YYYY.
            dob_pattern = re.compile(r'^([0-9]{1,2})[\/]([0-9]{1,2})[\/]([0-9]{4})$')
            result = dob_pattern.match(date_of_birth)

            # If regex has matched and we have 3 results, i.e. day,
            # month and year...
            if result and len(result.groups()) == 3:
                # Convert data from QueryDict to dict so we can
                # override date of birth.
                data = data.dict()

                day, month, year = result.groups()
                data['date-of-birth'] = '{}-{}-{}'.format(year, month, day)

        return data


class EnquiryFormBuilder(WagtailCaptchaFormBuilder):
    """
    Form builder that uses EnquiryFormDOBMixin in the form class.
    """
    def get_form_class(self):
        """
        Extend the form class with EnquiryFormDOBMixin.
        """
        form_class = super(EnquiryFormBuilder, self).get_form_class()
        return type(str('WagtailForm'), (EnquiryFormDOBMixin, form_class), self.formfields)
