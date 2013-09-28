# example usage:

# from rca.models import NewsItem, NewsItemLink
# from django_cluster import build_clusterable_model

# ClusterableNewsItem = build_clusterable_model(NewsItem, {'related_links': NewsItemLink})
# ni = ClusterableNewsItem(title='test', related_links=[
#    {'link': 'http://torchbox.com'}
# ])
# ni.related_links.all()


from django_cluster.manager import FakeManager


def build_clusterable_model(model, overrides):
    if not overrides:
        # no overriding of the original model is necessary
        return model

    Meta = type('Meta', (), {'proxy': True, 'app_label': 'django_cluster'})

    def init(self, **kwargs):
        kwargs_for_super = kwargs.copy()
        for (field_name, related_model) in overrides.items():
            field_val = kwargs_for_super.pop(field_name, [])
            related_instances = [
                related_model(**field_dict)
                for field_dict in field_val
            ]
            setattr(self, field_name, FakeManager(*related_instances))

        super(cls, self).__init__(**kwargs_for_super)

    dct = {
        'Meta': Meta,
        '__module__': 'django_cluster.models',
        '__init__': init
    }
    for name in overrides:
        dct[name] = None

    cls = type('Clusterable%s' % model.__name__, (model,), dct)
    return cls
