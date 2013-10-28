from django.db import models


class Indexed(object):
    @classmethod
    def get_content_type(cls):
        # Get parent content type
        parent_content_type = None
        for base in cls.__bases__:
            if issubclass(base, Indexed) and issubclass(base, models.Model):
                parent_content_type = base.get_content_type()
                break

        # Work out content type
        content_type = (cls._meta.app_label + "." + cls.__name__).lower()

        # Return content type
        if parent_content_type is not None:
            return parent_content_type + "_" + content_type
        else:
            return content_type

    @classmethod
    def get_toplevel_content_type(cls):
        # Get parent content type
        parent_content_type = None
        for base in cls.__bases__:
            if issubclass(base, Indexed) and issubclass(base, models.Model):
                return base.get_content_type()

        # At toplevel, return this content type
        return  (cls._meta.app_label + "." + cls.__name__).lower()

    indexed_fields = ()