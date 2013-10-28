# Constructor for test functions that determine whether an object passes some boolean condition
def test_exact(model, attribute_name, value):
    field = model._meta.get_field(attribute_name)
    # convert value to the correct python type for this field
    typed_value = field.to_python(value)
    return lambda obj: getattr(obj, attribute_name) == typed_value

class FakeQuerySet(object):
    def __init__(self, model, results):
        self.model = model
        self.results = results

    def all(self):
        return self

    def filter(self, **kwargs):
        filters = []  # a list of test functions; objects must pass all tests to be included
            # in the filtered list
        for key, val in kwargs.iteritems():
            key_clauses = key.split('__')
            if len(key_clauses) != 1:
                raise NotImplementedError("Complex filters with double-underscore clauses are not implemented yet")

            filters.append(test_exact(self.model, key_clauses[0], val))

        filtered_results = [
            obj for obj in self.results
            if all([test(obj) for test in filters])
        ]

        return FakeQuerySet(self.model, filtered_results)

    def get(self, **kwargs):
        results = self.filter(**kwargs)
        result_count = results.count()

        if result_count == 0:
            raise self.model.DoesNotExist("%s matching query does not exist." % self.model._meta.object_name)
        elif result_count == 1:
            return results[0]
        else:
            raise self.model.MultipleObjectsReturned(
                "get() returned more than one %s -- it returned %s!" % (self.model._meta.object_name, result_count)
            )

    def count(self):
        return len(self.results)

    def __getitem__(self, k):
        return self.results[k]

    def __iter__(self):
        return self.results.__iter__()

    def __nonzero__(self):
        return bool(self.results)

    def __repr__(self):
        return repr(list(self))

    def __len__(self):
        return len(self.results)

    ordered = True  # results are returned in a consistent order
