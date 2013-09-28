from django_cluster.queryset import FakeQuerySet

class FakeManager(object):
    def __init__(self, *results):
        self.queryset = FakeQuerySet(*results)

proxied_queryset_methods = ['all']

for name in proxied_queryset_methods:
    def method(self, *args, **kwargs):
        return getattr(self.queryset, name)(*args, **kwargs)
    setattr(FakeManager, name, method)
