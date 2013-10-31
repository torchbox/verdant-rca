from indexed import Indexed
from django.db import models
from django.conf import settings
from pyelasticsearch.exceptions import ElasticHttpNotFoundError
from elasticutils import get_es, S


class SearchResults(object):
    def __init__(self, model, query):
        self.model = model
        self.query = query
        self.count = query.count()

    def __getitem__(self, key):
        # Get list of primary keys
        if isinstance(key, slice):
            # Get primary keys
            pk_list = [result._source["pk"] for result in self.query[key]]

            # Get results
            results = self.model.objects.filter(pk__in=pk_list).prefetch_related("content_type")

            # Put results into a dictionary (using primary key as the key)
            results_dict = {str(result.pk): result for result in results}

            # Build new list with items in the correct order
            results_sorted = [results_dict[str(pk)] for pk in pk_list]

            # Return the list
            return results_sorted
        else:
            # Return a single item
            pk = self.query[key]._source["pk"]
            return self.model.objects.get(pk=pk)

    def __len__(self):
        return self.count


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

        INDEX_SETTINGS = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "ngram_analyzer": {
                            "type": "custom",
                            "tokenizer": "lowercase",
                            "filter": ["ngram"]
                        },
                        "edgengram_analyzer": {
                            "type": "custom",
                            "tokenizer": "lowercase",
                            "filter": ["edgengram"]
                        }
                    },
                    "tokenizer": {
                        "ngram_tokenizer": {
                            "type": "nGram",
                            "min_gram": 3,
                            "max_gram": 15,
                        },
                        "edgengram_tokenizer": {
                            "type": "edgeNGram",
                            "min_gram": 2,
                            "max_gram": 15,
                            "side": "front"
                        }
                    },
                    "filter": {
                        "ngram": {
                            "type": "nGram",
                            "min_gram": 3,
                            "max_gram": 15
                        },
                        "edgengram": {
                            "type": "edgeNGram",
                            "min_gram": 1,
                            "max_gram": 15
                        }
                    }
                }
            }
        }

        self.es.create_index(self.es_index, INDEX_SETTINGS)

    def add_type(self, model):
        # Get type name
        content_type = model.indexed_get_content_type()

        # Get indexed fields
        indexed_fields = model.indexed_get_indexed_fields()

        # Make field list
        fields = dict({
            "pk": dict(type="string", index="not_analyzed", store="yes"),
            "content_type": dict(type="string"),
        }.items() + indexed_fields.items())

        # Put mapping
        self.es.put_mapping(self.es_index, content_type, {
            content_type: {
                "properties": fields,
            }
        })

    def refresh_index(self):
        self.es.refresh(self.es_index)

    def _build_document(self, obj):
        # Get content type
        content_type = obj.indexed_get_content_type()

        # Build document
        doc = dict(pk=str(obj.pk), content_type=content_type)

        # Get indexed fields
        indexed_fields = obj.indexed_get_indexed_fields()

        # Add fields to document
        for field in indexed_fields.keys():
            doc[field] = getattr(obj, field)

            # Check if this field is callable
            if hasattr(doc[field], "__call__"):
                # Call it
                doc[field] = doc[field]()

        return doc

    def add(self, obj):
        # Doc must be a decendant of Indexed and be a django model
        if not isinstance(obj, Indexed) or not isinstance(obj, models.Model):
            return

        # Add to index
        self.es.index(self.es_index, obj.indexed_get_content_type(), self._build_document(obj))

    def add_bulk(self, obj_list):
        # This is just the same as above except it inserts lists of objects in bulk
        # Build documents
        #docs = [self._build_document(obj) for obj in obj_list if isinstance(obj, Indexed) and isinstance(obj, models.Model)]

        # Add to index
        #self.es.bulk_index(self.es_index, "indexed_item", docs)

        # TEMPORARY: We cannot bulk add a list of items with different types
        # TODO: Find a way to bulk add many items of different types
        for obj in obj_list:
            self.add(obj)

    def search(self, query_string, model, fields=None, filters={}):
        # Model must be a descendant of Indexed and be a djangi model
        if not issubclass(model, Indexed) or not issubclass(model, models.Model):
            return None

        # Query
        if fields:
            query = self.s.query_raw({
                "query_string": {
                    "query": query_string,
                    "fields": fields,
                }
            })
        else:
            query = self.s.query_raw({
                "query_string": {
                    "query": query_string,
                }
            })

        # Filter results by this content type
        query = query.filter(content_type__prefix=model.indexed_get_content_type())

        # Extra filters
        if filters:
            query = query.filter(**filters)

        # Return search results
        return SearchResults(model, query)