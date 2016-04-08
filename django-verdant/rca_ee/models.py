from django.shortcuts import render
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtailforms.models import AbstractForm, AbstractEmailForm, AbstractFormField
from wagtail.wagtaildocs.models import Document

import uuid

from .wtforms import ExtendedAbstractFormField, ExtendedAbstractForm, ExtendedAbstractEmailForm


class FormField(ExtendedAbstractFormField):
    """A single form field that is attached to a page."""
    page = ParentalKey('FormPage', related_name='form_fields')


class CourseDocument(models.Model):
    """
    A downloadable document that is specific for a certain course.
    """
    page = ParentalKey('FormPage', related_name='documents')

    for_course = models.TextField(
        help_text="The name of the course for which this document is valid. It will only be shown for registrations on this course. Please enter the name of the course exactly as it appears in the selection form below.",
    )

    document = models.ForeignKey(
        'wagtaildocs.Document',
        on_delete=models.CASCADE,
        related_name='+'
    )

    content_panels = [
        FieldPanel('for_course'),
        DocumentChooserPanel('document'),
    ]

CourseDocument.content_panels = [
    FieldPanel('for_course'),
    DocumentChooserPanel('document'),
]


class FormPage(ExtendedAbstractEmailForm):
    """
    A page for registering interest in a selection of courses.
    """
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    def serve(self, request):
        if request.method == 'POST':
            form = self.get_form(request.POST)

            if form.is_valid():
                self.process_form_submission(form)

                context = self.get_context(request)
                context['form'] = form
                # render the landing_page
                return render(
                    request,
                    self.landing_page_template,
                    context,
                )
        else:
            form = self.get_form()

        context = self.get_context(request)
        context['form'] = form
        return render(
            request,
            self.template,
            context
        )


FormPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('thank_you_text', classname="full"),
    InlinePanel('documents', label='Documents'),
    InlinePanel('form_fields', label="Form fields"),
]


class BookingFormField(ExtendedAbstractFormField):
    """A single form field that is attached to a booking form."""
    page = ParentalKey('BookingFormPage', related_name='form_fields')


class BookingFormPage(ExtendedAbstractForm):
    """
    A form for booking a specific course.
    """
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    def get_form_parameters(self):
        """Generate a new transaction id and put it in the form."""

        return {
            "initial": {
                "transaction_id": str(uuid.uuid4()),
            }
        }


BookingFormPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('thank_you_text', classname="full"),
    InlinePanel('form_fields', label="Form fields"),
]
