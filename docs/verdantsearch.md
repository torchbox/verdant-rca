# Verdant Search

## Configuration

### VERDANTSEARCH_ES_URLS

    VERDANTSEARCH_ES_URLS = ["http://localhost:9200"]

This is a list of URLs verdantsearch will use to find an ElasticSearch server

### VERDANTSEARCH_ES_INDEX

    VERDANTSEARCH_ES_INDEX = "verdant"

This is the name of the index that verdantsearch will use on the ElasticSearch server. The index will be created automatically.

### VERDANTSEARCH_RESULTS_TEMPLATE

    VERDANTSEARCH_RESULTS_TEMPLATE = "verdantsearch/search_results.html"

If you need to use a custom frontend search results page then override this value with the name of the template that you want to use.

The following variables will be passed through to the template
* query_string - This is the text that the user typed in to the search box
* search_results - This is a paginator for a list of core.Page objects in order of relevance
* is_ajax - This is set to true if the request was made using AJAX. Otherwise it is false

### VERDANTSEARCH_RESULTS_TEMPLATE_AJAX

    VERDANTSEARCH_RESULTS_TEMPLATE_AJAX = "verdantsearch/search_results.html"

This is similar to VERDANTSEARCH_RESULTS_TEMPLATE except that this sets the template to be used in AJAX requests. The same variables that are passed into the regular results template will be passed into this one too.

## Commands

### update_index

    python manage.py update_index

This command rebuilds the index from scratch. It is currently the only place where mappings are updated so you must run this command every time any changes are made to any indexed fields. You should also run this command after adding/updating/deleting any objects without using the UI (such as an import script).

It is reccomended to run this command once every 24 hours.

## Indexing

### Adding a model to the index

To make verdantsearch index a model, simply inherit the "Indexed" class and run the update_index command.

    from django.db import models
    from verdantsearch import Indexed


    class MyModel(models.Model, Indexed):
        title = models.TextField(max_length=255)

        indexed_fields = ("title", )

By default, only the primary key and content type of the objects will be added to the index. You must specify the fields you want to index by adding an indexed_fields attribute to the model and setting it to a list of the fields you would like to index.

The indexed fields attribute can be either a list, tuple, dictionary or a single string.

    indexed_fields = ("title", )
    indexed_fields = ["title"]
    indexed_fields = "title"
    indexed_fields = {
        "title": {
            "type": "string",
        }
    }

Dictionaries should be used to provide any extra information to the ElasticSearch mapping described here: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-core-types.html

### Preventing child models from being indexed

When a model is indexed, all of its child models are automatically indexed as well. You can override this behaviour by adding "indexed = False" into the child model.

    class MyModel(models.Model, Indexed):
        title = models.TextField(max_length=255)

        indexed_fields = ("title", )


    class MyChildModel(MyModel):
        indexed = False

### Preventing particular objects from being indexed

If you want to index some objects but not others, you need to create a method on the model called "object_indexed". This method will be called before inserting an object to the index. If this method returns False, the object will not be added to the index.

	class MyModel(models.Model, Indexed):
		title = models.TextField(max_length=255)

		indexed_fields = "title"

		def object_indexed(self):
			if self.title == "Don't index me!":
				return False
			return True

### Boosting fields

Sometimes, certian fields are more important than others (such as a title is usually more important than content)

f some fields are more important than others, you can boost them by adding a boost value to the field in the "indexed_fields" dictionary. This will increase the ranking of a result if the matched terms are in the boosted field.

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

### Setting the "search name"

The search name is useful when you want to display to your users the result type next to each result. In many cases you just want to display the name of the results' model (the default), but sometimes you may need to override this.

To override this, simply add a "search_name" attribute to the model. This can either be a simple text field or a property.

When search_name is text, every instance of the model will use it as the search name

    class MyModel(models.Model, Indexed):
        ...

        search_name = "My Model"

When search_name is a property, the property is called for every single result. This provides control of the search name for individual instances of the model.

    class MyModel(models.Model, Indexed):
        ...
        type = models.CharField(CHOICES=MYMODEL_TYPES)

        @property
        def search_name(self):
            return "My Model: " + self.type

## Searching

### A simple search

To search, firstly make an instance of the Search class (this sets up a connection to ElasticSearch)

You can then run the search method on this class. Don't forget to specify the model you are searching.

    from verdantsearch import Search
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

	from verdantsearch import searcher


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