# This file was sourced from github.com/django-extensions/django-extensions
# but split off into this project to allow patching for Django 1.3 to code
# around DeprecationWarnings

import datetime
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import simplejson
from django.utils.encoding import smart_unicode

# from south.modelsinspector import add_introspection_rules

class UUIDField(models.CharField):
    """
    Unique identifier field, using Pythons UUID library
    """

    # add_introspection_rules([], ["^core\.models\.UUIDField"])

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 64)
        kwargs['blank'] = True
        self.generate_if_blank = kwargs.pop('generate_if_blank', True)

        models.CharField.__init__(self, *args, **kwargs)

    def pre_save(self, model_instance, add):
        # Only set on creation if already blank. This is because duplicated models (e.g. pages' different versions) may not be unique.
        if add and self.generate_if_blank and getattr(model_instance, self.attname) == '':
            value = uuid.uuid4().hex
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(models.CharField, self).pre_save(model_instance, add)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.CharField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)


"""
JSONField automatically serializes most Python terms to JSON data.
Creates a TEXT field with a default value of "{}".

 from django.db import models
 from django_extensions.db.fields import json

 class LOL(models.Model):
     extra = json.JSONField()
"""


class JSONEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            assert settings.TIME_ZONE == 'UTC'
            return obj.strftime('%Y-%m-%dT%H:%M:%SZ')
        return simplejson.JSONEncoder.default(self, obj)


def dumps(value):
    try:
        assert isinstance(value, dict)
    except AssertionError:
        try:
            assert isinstance(value, list)
        except AssertionError:
            raise

    return JSONEncoder().encode(value)


def loads(txt):
    value = simplejson.loads(
        txt,
        parse_float=Decimal,
        encoding=settings.DEFAULT_CHARSET
    )
    try:
        assert isinstance(value, dict)
    except AssertionError:
        try:
            assert isinstance(value, list)
        except AssertionError:
            raise
    return value


class JSONDict(dict):
    """
    Hack so repr() called by dumpdata will output JSON instead of
    Python formatted data.  This way fixtures will work!
    """
    def __repr__(self):
        return dumps(self)


class JSONList(list):
    """
    Similar to JSONDict, but for Lists/Arrays
    """
    def __repr__(self):
        return dumps(self)


class JSONField(models.TextField):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly.  Main thingy must be a dict or a list (ie: JS map or array) """

    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        if 'default' not in kwargs:
            kwargs['default'] = '{}'
        models.TextField.__init__(self, *args, **kwargs)

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if not value:
            return {}
        elif isinstance(value, basestring):
            res = loads(value)
            try:
                assert isinstance(res, dict)
                return JSONDict(**res)
            except AssertionError:
                try:
                    assert isinstance(res, list)
                    return JSONList(res)
                except AssertionError:
                    raise
        else:
            return value

    def get_db_prep_save(self, value, **kwargs):
        """Convert our JSON object to a string before we save"""

        if not isinstance(value, (list, dict)):
            # NOTE: this is a little ruthless, but works
            return super(JSONField, self).get_db_prep_save(
                "",
                **kwargs
            )
        else:
            return super(JSONField, self).get_db_prep_save(
                dumps(value),
                **kwargs
            )

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.TextField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)