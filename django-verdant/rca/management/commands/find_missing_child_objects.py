import json

from django.core.management.base import NoArgsCommand

from wagtail.wagtailcore.models import get_page_types


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        for content_type in get_page_types():
            print "scanning %s" % content_type.name

            page_class = content_type.model_class()

            if not hasattr(page_class._meta, 'child_relations'):
                continue

            relations_by_name = {}
            for rel in page_class._meta.child_relations:
                relations_by_name[rel.get_accessor_name()] = rel

            for page in page_class.objects.all():
                revision = page.revisions.order_by('-created_at').first()
                if not revision:
                    continue

                revision_data = json.loads(revision.content_json)

                for (rel_name, rel) in relations_by_name.iteritems():
                    for child in revision_data.get(rel_name, []):
                        pk = child.get('pk')
                        if pk:
                            try:
                                rel.model.objects.get(pk=pk)
                            except rel.model.DoesNotExist:
                                print "No %s with ID %d found (linked from page %d)" % (rel.model.__name__, pk, page.id)
