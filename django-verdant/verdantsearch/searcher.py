from search import Search


class Searcher(object):
    def __init__(self, fields, **kwargs):
        self.fields = fields

    def __get__(self, instance, cls):
        def dosearch(query_string, **kwargs):
            return Search(**kwargs).search(query_string, model=cls, fields=self.fields)
        return dosearch