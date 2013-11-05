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
* do_search - This is set to true when a search is taking place, otherwise it will return False
* query_string - This is the text that the user typed in to the search box
* search_results - This is a paginator containing a list of core.Page objects in order of relevance

## Commands

### update_index

    python manage.py update_index

This command rebuilds the index from scratch. It is currently the only place where mappings are updated so you must run this command every time any changes are made to any indexed fields. You should also run this command after adding/updating/deleting any objects without using the UI (as these changes don't get automatically picked up).

## Indexing

### Adding a model to the index

To make verdantsearch index a model, simply inherit the "Indexed" class
Don't forget to run the "update_index" command once you've done this!

    from django.db import models
    from verdantsearch import Indexed


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

If you want to be able to find objects by only typing part of a word (eg. search for "Hel" and get "Hello" in the results), you need to enable ngrams on the field. You can do this by setting "analyzer" to "edgengram_analyzer" in the fields configuration.

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

    from verdantsearch import Search
    from core.models import Page
    Search().search(query_string, model=Page)

### Searching on specific fields

    Search().search(query_string, model=Page, fields=["title"])

### Filters

    Search().search(query_string, model=Page, filters=dict(live=True))

## Searchers

### A simple searcher

    class MyModel(models.Model, Indexed):
        title = models.TextField(max_length=255)

        indexed_fields = {
            "title": {
                "type": "string",
                "analyzer": "edgengram_analyzer",
            }
        }

        search = Searcher(None)

    MyModel.search("Hello")

### Searching on specific fields

	title_search = Searcher(["title"])


### Filters

	search_live = Searcher(None, filters=dict(live=True))