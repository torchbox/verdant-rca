from django.forms import ModelForm

from core.models import Page
from verdantadmin.panels import FieldPanel


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
            # defining a concrete subclass, so ensure that form, panels etc are defined
            if 'form' not in dct:
                # build a basic ModelForm from the model that we've (hopefully) been passed
                try:
                    model = dct['model']
                except KeyError:
                    raise Exception("Definition of %s must specify either a 'form' attribute or a 'model' attribute" % name)

                cls.form = build_model_form_class(model)

            if 'panels' not in dct:
                # in the absence of an explicit panel list declaration,
                # compile a passable one by turning each field in cls.form into
                # an individual FieldPanel
                cls.panels = [FieldPanel(field_name) for field_name in cls.form.base_fields]


class AdminHandler(object):
    __metaclass__ = AdminHandlerBase

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)

        # construct the form instance that spans all panel instances
        self.form_instance = self.form(*args, instance=instance)

        # create each panel instance, handing it the submitted data, model instance and form instance
        self.panel_instances = [
            panel.get_panel_instance(*args, instance=instance, form=self.form_instance)
            for panel in self.panels
        ]

    def is_valid(self):
        # overall submission is valid if the form is valid and all panels are valid
        result = self.form_instance.is_valid()
        for panel in self.panel_instances:
            result &= panel.is_valid()
        return result

    def save(self, commit=True):
        self._pre_save()

        result = self.form_instance.save(commit=commit)

        if commit:
            self._post_save()

        return result

    def _pre_save(self):
        for panel in self.panel_instances:
            panel.pre_save()

    def _post_save(self):
        for panel in self.panel_instances:
            panel.post_save()


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
