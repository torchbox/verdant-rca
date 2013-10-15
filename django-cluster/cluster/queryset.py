class FakeQuerySet(object):
    def __init__(self, *results):
        self.results = results

    def all(self):
        return self

    def filter(self, **kwargs):
        # TODO: when this performs real filtering, we'll need to get tricksy with our
        # BaseInlineFormSet inheritance in forms.py, to skip over the step where the
        # queryset gets forcibly filtered down to nothing when the primary key on the
        # parent model is not populated.
        return self

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
