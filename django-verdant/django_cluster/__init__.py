# example usage:

# from rca.models import NewsItem
# from django_cluster import build_cluster
# ni = build_cluster(NewsItem, title='test', related_links=[
#    {'link': 'http://torchbox.com'}
# ])


def build_cluster(model, **kwargs):
    fields = dict([(field.name, field) for field in model._meta.fields])
    related_objects = dict([(field.get_accessor_name(), field) for field in model._meta.get_all_related_objects()])

    field_kwargs = {}
    proxy_class_dict = {}

    for key, val in kwargs.items():
        if key in fields:
            # this is an ordinary field - pass on to kwargs for this model
            field_kwargs[key] = val
        elif key in related_objects:
            related_model = related_objects[key].model
            related_instances = [
                build_cluster(related_model, **related_fields)
                for related_fields in val
            ]

            proxy_class_dict[key] = related_instances
        else:
            raise TypeError("build_cluster received an unexpected kwarg '%s'" % key)

    if proxy_class_dict:
        class Meta:
            proxy = True
            app_label = 'django_cluster'

        proxy_class_dict['Meta'] = Meta
        proxy_class_dict['__module__'] = 'django_cluster.models'
        proxy_model = type('Proxied%s' % model.__name__, (model,), proxy_class_dict)
        return proxy_model(**field_kwargs)
    else:
        # nothing to override; just instantiate model directly
        return model(**field_kwargs)
