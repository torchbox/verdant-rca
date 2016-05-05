import json

import django
from django.db import models
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailforms.models import FORM_FIELD_CHOICES, AbstractFormField, AbstractForm, AbstractEmailForm
from wagtail.wagtailforms.forms import FormBuilder
from wagtailcaptcha.models import WagtailCaptchaForm, WagtailCaptchaEmailForm, WagtailCaptchaFormBuilder


FORM_FIELD_CHOICES = FORM_FIELD_CHOICES + (
    ('multigroup', _('Grouped option field (extended syntax, see documentation)')),
    ('hidden', _('Hidden field (not editable by user)')),
)

class ExtendedAbstractFormField(AbstractFormField):
    """
    Some more options added to the form fields.
    """

    # unfortunately we cannot override the field definition
    # so we have to create a new one and ignore the old one.
    # yes, that is wasted space but not much anyway
    new_field_type = models.CharField(verbose_name=_('Field type'), max_length=16, choices=FORM_FIELD_CHOICES)

    def save(self, *args, **kwargs):
        self.field_type = self.new_field_type
        return super(AbstractFormField, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ['sort_order']

    # we have to repeat them here because we re-named one of the fields
    panels = [
        FieldPanel('label'),
        FieldPanel('help_text'),
        FieldPanel('required'),
        FieldPanel('new_field_type', classname="formbuilder-type"),
        FieldPanel('choices', classname="formbuilder-choices"),
        FieldPanel('default_value', classname="formbuilder-default"),
    ]


class ExtendedFormBuilder(WagtailCaptchaFormBuilder):

    def __init__(self, fields):
        super(ExtendedFormBuilder, self).__init__(fields)
        self.FIELD_TYPES.update({
            'hidden': ExtendedFormBuilder.create_hidden_field,
            'multigroup': ExtendedFormBuilder.create_grouped_dropdown_field,
        })

    def create_hidden_field(self, field, options):
        options['widget'] = django.forms.widgets.HiddenInput
        return django.forms.CharField(**options)

    def create_grouped_dropdown_field(self, field, options):
        choices = field.choices
        choices = json.loads(choices)

        choices = [
            (groupname.strip(), [(o.strip(), o.strip()) for o in opts])
            for groupname, opts in choices
        ]

        options['choices'] = choices
        return django.forms.ChoiceField(**options)


class ExtendedAbstractForm(WagtailCaptchaForm):

    def __init__(self, *args, **kwargs):
        super(ExtendedAbstractForm, self).__init__(*args, **kwargs)
        self.form_builder = ExtendedFormBuilder


class ExtendedAbstractEmailForm(WagtailCaptchaEmailForm):

    def __init__(self, *args, **kwargs):
        super(ExtendedAbstractEmailForm, self).__init__(*args, **kwargs)
        self.form_builder = ExtendedFormBuilder


