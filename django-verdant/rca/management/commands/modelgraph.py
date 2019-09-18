from django.apps import apps
from django.core.management.base import NoArgsCommand
from django.contrib.contenttypes.models import ContentType

from modelcluster.fields import ParentalKey
from wagtail.wagtailcore.models import Page
from taggit.managers import TaggableManager
from taggit.models import Tag

from rca.models import RcaImage, Advert
from taxonomy.models import School, Programme, Area, DegreeLevel
from wagtail.wagtaildocs.models import Document


class Command(NoArgsCommand):
    def process_relationship(self, field, model):
        if field.name == 'page_ptr':
            pass
        elif field.one_to_many and isinstance(field.field, ParentalKey):
            # Found a child relation
            for child_field in field.related_model._meta.get_fields():
                if child_field.is_relation and child_field != field.field:
                    for rels in self.process_relationship(child_field, model):
                        yield [(field.name, field.model, field.related_model)] + rels

        elif field.concrete:
            if field.related_model is Page:
                # This field links to the generic "Page" type, find actual page types that have been linked to
                for content_type_id in Page.objects.filter(id__in=field.model.objects.values_list(field.name + '_id', flat=True)).select_related('content_type').values_list('content_type', flat=True):
                    content_type = ContentType.objects.get(id=content_type_id)
                    yield [(field.name, field.model, content_type.model_class())]
            else:
                yield [(field.name, field.model, field.related_model)]

    def handle_noargs(self, **options):
        allrels = []
        allmodels = []
        for model in apps.get_models():
            if not issubclass(model, Page):
                continue

            allmodels.append(model)

            # Find relationships
            for field in model._meta.get_fields():
                # Not interested in base fields
                if field.model is Page:
                    continue

                if field.is_relation:
                    for rels in self.process_relationship(field, model):
                        allrels.append(rels)


        for model in allmodels:
            print model.__name__, ";"

        for rel in allrels:
            if rel[-1][2] not in [RcaImage, Tag, School, Programme, Area, DegreeLevel, Advert, Document] and rel[0][1].__name__ != rel[-1][2].__name__:
                print rel[0][1].__name__, "->", rel[-1][2].__name__, ";"

