from  wagtail.wagtailadmin.forms import WagtailAdminPageForm


class StaffPageForm(WagtailAdminPageForm):
    def clean(self):
        cleaned_data = super(StaffPageForm, self).clean()

        for form in self.formsets.get('roles', []):
            self.clean_staff_page_role_form(form, cleaned_data)

    def clean_staff_page_role_form(self, form, staff_page_cleaned_data):
        if not form.is_valid():
            return

        area = form.cleaned_data.get('area')
        location = form.cleaned_data.get('location')
        programme = form.cleaned_data.get('programme')
        school = form.cleaned_data.get('school')
        staff_type = staff_page_cleaned_data.get('staff_type')

        # Will display all errors at the same time, so need to create a dict
        errors = {x: [] for x in ('area', 'location', 'programme', 'school')}

        # Staff location must be only for technical staff
        if staff_type != 'technical' and location:
            errors['location'].append('Location can be assigned only to technical staff')

        # School and programme must be only for academic staff
        if staff_type != 'academic':
            if school:
                errors['school'].append('School can be assigned only to academic staff.')

            if programme:
                errors['programme'].append('Programme can be only assigned to academic staff.')

        # Area cannot be filled in when staff is non-academic/administrative
        if staff_type not in ('academic', 'administrative') and area:
            errors['area'].append('Area can be only assigned to academic or administrative staff.')

        # If there are any errors in our dict, raise them.
        if any(errors.itervalues()):
            for field_name, field_errors in errors.items():
                for field_error in field_errors:
                    form.add_error(field_name, field_error)
