from indexed import Indexed
from django.db import models
from django.conf import settings
from pyelasticsearch.exceptions import ElasticHttpNotFoundError
from elasticutils import get_es, S


class SearchResults(object):
    def __init__(self, model, query):
        self.model = model
        self.query = query

    def __getitem__(self, key):
        # Get list of primary keys
        if isinstance(key, slice):
            # Return a query set
            pk_list = [result._source["pk"] for result in self.query[key]]
            return self.model.objects.filter(pk__in=pk_list)
        else:
            # Return a single item
            pk = self.query[key]._source["pk"]
            return self.model.objects.get(pk=pk)

    def __len__(self):
        return len(self.query)


class Search(object):
    def __init__(self, **kwargs):
        # Get settings
        self.es_urls = kwargs.get("es_urls", getattr(settings, "VERDANTSEARCH_ES_URLS", ["http://localhost:9200"]))
        self.es_index = kwargs.get("es_index", getattr(settings, "VERDANTSEARCH_ES_INDEX", "verdant"))

        # Get ElasticSearch interface
        self.es = get_es(urls=self.es_urls)
        self.s = S().es(urls=self.es_urls).indexes(self.es_index)

    def reset_index(self):
        try:
            self.es.delete_index(self.es_index)
        except ElasticHttpNotFoundError:
            pass

        self.es.create_index(self.es_index)

    def refresh_index(self):
        self.es.refresh(self.es_index)

    def _build_document(self, obj):
        # Get content type
        content_type = obj.get_content_type()

        # Build document
        doc = dict(pk=str(obj.pk), content_type=content_type)

        # Add fields to document
        for field in obj.indexed_fields:
            doc[field] = getattr(obj, field)

        return doc

    def add(self, obj):
        # Doc must be a decendant of Indexed and be a django model
        if not isinstance(obj, Indexed) or not isinstance(obj, models.Model):
            return

        # Add to index
        self.es.index(self.es_index, "indexed_item", self._build_document(obj))

    def add_bulk(self, obj_list):
        # This is just the same as above except it inserts lists of objects in bulk
        # Build documents
        docs = [self._build_document(obj) for obj in obj_list if isinstance(obj, Indexed) and isinstance(obj, models.Model)]

        # Add to index
        self.es.bulk_index(self.es_index, "indexed_item", docs)

    def search(self, query_string, model, fields=None):
        # Model must be a descendant of Indexed and be a djangi model
        if not issubclass(model, Indexed) or not issubclass(model, models.Model):
            return None

        # If fields are not set, use the models indexed_fields
        if not fields:
            fields = list(model.indexed_fields)

        # Query
        query = self.s.query_raw({
                "query_string": {
                    "query": query_string,
                    "fields": fields,
                }
            })

        # Filter results by this content type
        query = query.filter(content_type__prefix=model.get_content_type())

        # Return search results
        return SearchResults(model, query)