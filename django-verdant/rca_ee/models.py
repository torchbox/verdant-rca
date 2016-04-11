import json

from django.core.exceptions import ValidationError
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


class CourseNeedsUpload(models.Model):
    """Define that a course needs a portfolio upload before you can register interest."""

    page = ParentalKey('FormPage', related_name='upload_necessary')

    for_course = models.TextField(
        help_text="The name of the course for which a portfolio upload is necessary before registering interest. Please enter the name of the course exactly as it appears in the selection form below.",
    )

    content_panels = [
        FieldPanel('for_course'),
    ]


class FormPage(ExtendedAbstractEmailForm):
    """
    A page for registering interest in a selection of courses.
    """
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    def serve(self, request):
        context = self.get_context(request)
        context['upload_vals'] = json.dumps([
            d.for_course.lower() for d in self.upload_necessary.all()
        ])

        if request.method == 'POST':
            form = self.get_form(request.POST)

            try:
                if form.is_valid():
                    portfolio_necessary_courses = set([
                        d.for_course.lower().strip() for d in self.upload_necessary.all()
                    ])
                    context['selected_courses'] = selected_courses = set(
                        [c.lower().strip() for c in form.cleaned_data.get('course', ())]
                        + [c.lower().strip() for c in form.cleaned_data.get('masterclasses', ())]
                        + [c.lower().strip() for c in form.cleaned_data.get('residencies', ())]
                        + [c.lower().strip() for c in form.cleaned_data.get('workshops', ())]
                    )

                    if selected_courses & portfolio_necessary_courses:
                        # a portfolio upload is necessary
                        # check if a portfolio was uploaded and if not, raise a ValidationError
                        if "portfolio" not in request.FILES:
                            context['portfolio_upload_error'] = True
                            raise ValidationError('Portfolio upload is necessary')
                        else:
                            # store the portfolio file as a document
                            from wagtail.wagtaildocs.models import Document
                            d = Document(
                                uploaded_by_user=None,
                                title='Portfolio upload for {} {}'.format(
                                    form.cleaned_data['first-name'],
                                    form.cleaned_data['last-name']
                                ),
                                file=request.FILES['portfolio'],
                            )
                            d.save()
                            form.cleaned_data['portfolio_document_id'] = d.id

                    self.process_form_submission(form)

                    context['form'] = form
                    # render the landing_page
                    return render(
                        request,
                        self.landing_page_template,
                        context,
                    )
            except ValidationError:
                pass
        else:
            form = self.get_form()

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
    InlinePanel('upload_necessary', label='Needs portfolio update'),
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
