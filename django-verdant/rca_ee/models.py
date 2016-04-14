import json

from django.core.exceptions import ValidationError
from django.db.models import ForeignKey
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

    def for_course_lower(self):
        return self.for_course.lower().strip()

    def save(self, *args, **kwargs):
        self.full_clean()
        super(CourseDocument, self).save(*args, **kwargs)

    def clean(self):
        self.for_course = self.for_course.strip()

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

    terms_and_conditions = ForeignKey(
        Document,
        verbose_name='Terms and Conditions',
        help_text='This document will be shown as the Terms and Conditions document.',
        blank=True, null=True,
    )

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
    DocumentChooserPanel('terms_and_conditions'),
    InlinePanel('documents', label='Documents'),
    InlinePanel('form_fields', label="Form fields"),
]


class BookingFormField(ExtendedAbstractFormField):
    """A single form field that is attached to a booking form."""
    page = ParentalKey('BookingFormPage', related_name='form_fields')


class CourseNeedsUpload(models.Model):
    """Indicator that a course can only be booked after sending a portfolio."""

    page = ParentalKey('BookingFormPage', related_name='portfolio_necessary')

    for_course = models.TextField(
        help_text="The name of the course for which a portfolio upload is necessary before registering interest. Please enter the name of the course exactly as it appears in the selection form below.",
    )
    content_panels = [
        FieldPanel('for_course'),
    ]


class BookingFormPage(ExtendedAbstractForm):
    """
    A form for booking a specific course.
    """
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)
    terms_and_conditions = ForeignKey(
        Document,
        verbose_name='Terms and Conditions',
        help_text='This document will be shown as the Terms and Conditions document.',
        blank=True, null=True,
    )

    def get_form_class(self):

        that = self
        class FormClass(super(ExtendedAbstractForm, self).get_form_class()):

            def clean(self):
                cleaned_data = super(FormClass, self).clean()
                print(cleaned_data)
                course = cleaned_data.get('course').lower().strip()
                portfolio_necessary_courses = set([c.for_course.lower().strip() for c in that.portfolio_necessary.all()])
                if course in portfolio_necessary_courses and not cleaned_data.get('portfolio-requirement'):
                    print("portfolio requirement not fulfilled")
                    self.add_error('portfolio-requirement', 'You must confirm the portfolio requirement to book this course.')

                return cleaned_data

        return FormClass

    def get_form_parameters(self):
        """Generate a new transaction id and put it in the form."""

        return {
            "initial": {
                "transaction_id": str(uuid.uuid4()),
            }
        }

    def serve(self, request):
        context = self.get_context(request)
        context['portfolio_necessary_courses'] = [c.for_course.lower().strip() for c in self.portfolio_necessary.all()]
        context['portfolio_necessary_courses_json'] = json.dumps(context['portfolio_necessary_courses'])

        errors = False
        if request.method == 'POST':
            form = self.get_form(request.POST)

            if form.is_valid():
                self.process_form_submission(form)

                context['form'] = form
                # render the landing_page
                return render(
                    request,
                    self.landing_page_template,
                    context,
                )
            else:
                errors = True
        else:
            form = self.get_form()

        context['form'] = form
        return render(
            request,
            self.template,
            context,
            status=200 if not errors else 400
        )

BookingFormPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('thank_you_text', classname="full"),
    DocumentChooserPanel('terms_and_conditions'),
    InlinePanel('portfolio_necessary', label="Portfolio necessary"),
    InlinePanel('form_fields', label="Form fields"),
]
