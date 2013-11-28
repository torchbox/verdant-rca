# Verdant Search

## Configuration

### VERDANTSEARCH_ES_URLS

    VERDANTSEARCH_ES_URLS = ["http://localhost:9200"]

This is a list of URLs verdantsearch will use to find ElasticSearch

### VERDANTSEARCH_ES_INDEX

    VERDANTSEARCH_ES_INDEX = "verdant"

This is the name of the index that verdantsearch will use for indexing/searching

### VERDANTSEARCH_RESULTS_TEMPLATE

    VERDANTSEARCH_RESULTS_TEMPLATE = "verdantsearch/search_results.html"

If you want to use a frontend search results page then override this value with the name of the template that you want to use for search results.

The following variables will be passed through to the template
* do_search - This is set to true when a search is taking place
* query_string - This is the text that the user typed in to the search box
* search_results - This is a paginator for a list of core.Page objects in order of relevance

## Commands

### update_index

    python manage.py update_index

This command rebuilds the index from scratch. It is currently the only place where mappings are updated so you must run this command every time any changes are made to any indexed fields. You should also run this command after adding/updating/deleting any objects without using the UI (such as an import script).

## Indexing

### Adding a model to the index

To make verdantsearch index a model, simply inherit the "Indexed" class.

    from django.db import models
    from verdant.verdantsearch import Indexed


    class MyModel(models.Model, Indexed):
        title = models.TextField(max_length=255)

        indexed_fields = ("title", )

The indexed fields attribute can be either a list, tuple, dictionary or a single string.

    indexed_fields = ("title", )
    indexed_fields = ["title"]
    indexed_fields = "title"
    indexed_fields = {
        "title": {
            "type": "string",
        }
    }

Dictionaries must be used to provide any extra information to the ElasticSearch mapping described here: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-core-types.html

### Preventing child models from being indexed

When a model is indexed, all of its child models are automatically indexed as well. You can override this behaviour by adding "indexed = False" into the child model.

    class DontIndex(IndexedModel):
        indexed = False

### Preventing particular objects from being indexed

If you want index some objects but not others, just add a new method to the model called "object_indexed". This method will be called before adding an object to the index. If this method returns False, the object will not be added to the index.

	class MyModel(models.Model, Indexed):
		title = models.TextField(max_length=255)

		indexed_fields = "title"

		def object_indexed(self):
			if self.title == "Don't index me!":
				return False
			return True

### Boosting fields

If some fields are more important than others, you can boost them by adding a boost value to the field in the "indexed_fields" dictionary.

You must run the "update_index" after adding this.

    class MyModel(models.Model, Indexed):
        title = models.TextField(max_length=255)
        content = models.TextField()

        indexed_fields = {
            "title": {
                "type": "string",
                "boost": 10,
            },
            "content": {
                "type": "string",
                "boost": 1,
            }
        }

### Partial term matching

If you want to find objects by only typing part of a word (eg. search for "Hel" instead of "Hello"), you need to enable ngrams on the field. You can do this by setting "analyzer" to "edgengram_analyzer" in the fields configuration.

Like boosting fields, you must run the "update_index" after adding this.

    class MyModel(models.Model, Indexed):
        title = models.TextField(max_length=255)

        indexed_fields = {
            "title": {
                "type": "string",
                "analyzer": "edgengram_analyzer",
            }
        }

## Searching

### A simple search

To search, firstly make an instance of the Search class (this sets up a connection to ElasticSearch)

You can then run the search method on this class. Don't forget to specify the model you are searching.

    from verdant.verdantsearch import Search
    from core.models import Page


    results = Search().search(query_string, model=Page)

### Searching on specific fields

    results = Search().search(query_string, model=Page, fields=["title"])

### Filters

https://elasticutils.readthedocs.org/en/latest/searching.html#filters-filter

    results = Search().search(query_string, model=Page, filters=dict(live=True))

## Searchers

Searchers allow you to add search methods into the class. This makes searching much easier as to search you only have to call a class method in order to search.

### A simple searcher

Creating searchers is very similar to just adding an extra field to the model.
The first arguement is a list of fields this searcher will search. Set this to None to search all fields.

	from verdant.verdantsearch import searcher


    class MyModel(models.Model, Indexed):
        title = models.TextField(max_length=255)

        indexed_fields = {
            "title": {
                "type": "string",
                "analyzer": "edgengram_analyzer",
            }
        }

        search = Searcher(None)

To search this model, simply do:

    results = MyModel.search("Hello")

### Searching on specific fields

To search specific fields, set the first arguement to a list of fields

	title_search = Searcher(["title"])

### Filters

Like the search method above, you can add filters by just setting the filters arguement to a dictionary of filters.

	search_live = Searcher(None, filters=dict(live=True))