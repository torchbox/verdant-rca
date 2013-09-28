class FakeQuerySet(object):
    def __init__(self, *results):
        self.results = results

    def all(self):
        return self

    def __getitem__(self, k):
        return self.results[k]

    def __iter__(self):
        return self.results.__iter__()

    def __nonzero__(self):
        return bool(self.results)

    def __repr__(self):
        return repr(list(self))
