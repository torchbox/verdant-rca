from django.forms import ModelForm
from django.utils.safestring import mark_safe

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


class AdminHandler(object):
    __metaclass__ = AdminHandlerBase

    def __init__(self, *args, **kwargs):
        if 'form' in kwargs:
            self.form = kwargs['form']
            instance = self.form.instance
        else:
            instance = kwargs.get('instance', None)

            # construct the form instance that spans all panel instances
            self.form = self.__class__.form(*args, instance=instance)

        # do we have an explicit list of panel definitions?
        try:
            panel_definitions = self.__class__.panels
        except AttributeError:
            # infer a list of panel definitions from the form contents
            visible_field_names = [f.name for f in self.form.visible_fields()]
            panel_definitions = [FieldPanel(field_name) for field_name in visible_field_names]

        # create each panel instance, handing it the submitted data, model instance and form instance
        self.panels = [
            panel.get_panel_instance(*args, instance=instance, form=self.form)
            for panel in panel_definitions
        ]

    def is_valid(self):
        # overall submission is valid if the form is valid and all panels are valid
        result = self.form.is_valid()
        for panel in self.panels:
            result &= panel.is_valid()
        return result

    def save(self, commit=True):
        self._pre_save()

        result = self.form.save(commit=commit)

        if commit:
            self._post_save()

        return result

    def _pre_save(self):
        for panel in self.panels:
            panel.pre_save()

    def _post_save(self):
        for panel in self.panels:
            panel.post_save()

    def render(self):
        # find out which form fields will be rendered by panels
        fields_rendered_by_panels = set()
        for panel in self.panels:
            for field in panel.rendered_fields():
                fields_rendered_by_panels.add(field)

        panel_html = "".join([panel.render() for panel in self.panels])
        other_fields_html = "".join([
            unicode(self.form[field])
            for field in self.form.fields if field not in fields_rendered_by_panels
        ])

        return mark_safe(panel_html + other_fields_html)

    def render_setup_js(self):
        """
        return a string of the JS code to be executed once the HTML has been rendered
        """
        js_snippets = [panel.render_js() for panel in self.panels]
        # discard the empty ones
        js_snippets = [s for s in js_snippets if s]

        return mark_safe("\n".join(js_snippets))


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
