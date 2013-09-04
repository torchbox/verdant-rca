from django.forms import ModelForm

from core.models import Page


ADMIN_HANDLERS = {}


def build_model_form_class(model_class):
    class MyModelForm(ModelForm):
        class Meta:
            model = model_class

            if issubclass(model_class, Page):
                exclude = ['content_type', 'path', 'depth', 'numchild']

    return MyModelForm


class AdminHandlerBase(type):
    """Metaclass for AdminHandler"""
    def __init__(cls, name, bases, dct):
        super(AdminHandlerBase, cls).__init__(name, bases, dct)

        if name != 'AdminHandler':
            # defining a concrete subclass, so ensure that model, form, fields etc are defined
            if 'model' not in dct:
                raise Exception("Definition of %s does not specify a 'model' attribute" % name)

            if 'form' not in dct:
                cls.form = build_model_form_class(cls.model)

            if 'inlines' not in dct:
                cls.inlines = []


class AdminHandler(object):
    __metaclass__ = AdminHandlerBase

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)

        self.form_instance = self.form(*args, instance=instance)

        self.inline_instances = [
            inline(*args, instance=instance)
            for inline in self.inlines
        ]

    def is_valid(self):
        result = self.form_instance.is_valid()
        for inline in self.inline_instances:
            result &= inline.is_valid()
        return result

    def save(self, commit=True):
        result = self.form_instance.save(commit=commit)
        if commit:
            self.save_inlines()
        return result

    def save_inlines(self, commit=True):
        for inline in self.inline_instances:
            inline.save(commit=commit)


def build_admin_handler_class(model_class):
    class MyAdminHandler(AdminHandler):
        model = model_class

    return MyAdminHandler


def get_admin_handler_for_model(model_class):
    if model_class not in ADMIN_HANDLERS:
        ADMIN_HANDLERS[model_class] = build_admin_handler_class(model_class)

    return ADMIN_HANDLERS[model_class]


def register(model_class, admin_handler):
    ADMIN_HANDLERS[model_class] = admin_handler
