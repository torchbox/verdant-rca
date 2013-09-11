from django.forms.models import modelform_factory
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from core.models import Page
from verdantadmin.panels import FieldPanel


ADMIN_HANDLERS = {}


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

                # If this form is for a Page object, omit the tree-related fields created by
                # Treebeard.
                # TODO: find a less hard-code-y way of achieving this. Possible approaches:
                # * inject an editable=False flag into those model fields, which they really
                #   should have had in the first place. Django doesn't like us overriding
                #   fields from a superclass, though:
                #   https://docs.djangoproject.com/en/1.5/topics/db/models/#field-name-hiding-is-not-permitted
                # * implement a PageAdminHandlerBase subclass of this, which adds these to
                #   the exclude list, and have all adminhandlers for page objects descending
                #   from that. (Will need us to refactor things to support abstract subclasses
                #   of AdminHandler...)
                exclude = []
                if issubclass(model, Page):
                    exclude = ['content_type', 'path', 'depth', 'numchild']

                widgets = {}  # initially, no widgets will be overridden
                if 'panels' in dct:
                    # give panels the chance to override widgets
                    for panel_def in dct['panels']:
                        widgets.update(panel_def.widgets())

                cls.form = modelform_factory(model, exclude=exclude, widgets=widgets)


def panel_for_field(field_name, field_def):
    try:
        panel_class = field_def.widget.get_panel()
    except AttributeError:
        panel_class = FieldPanel

    return panel_class(field_name)


class AdminHandler(object):
    __metaclass__ = AdminHandlerBase

    can_delete = False

    def __init__(self, data=None, files=None, **kwargs):
        self.data = data
        self.files = files

        if 'form' in kwargs:
            self.form = kwargs['form']
            instance = self.form.instance
        else:
            instance = kwargs.get('instance', None)

            # construct the form instance that spans all panel instances
            self.form = self.__class__.form(data, files, instance=instance)

        # do we have an explicit list of panel definitions?
        try:
            panel_definitions = self.__class__.panels
        except AttributeError:
            # infer a list of panel definitions from the form contents
            visible_field_names = [f.name for f in self.form.visible_fields()]
            panel_definitions = [
                panel_for_field(field_name, self.form.fields[field_name])
                for field_name in visible_field_names
            ]

        # create each panel instance, handing it the submitted data, model instance and form instance
        self.panels = [
            panel_class(data, files, instance=instance, form=self.form)
            for panel_class in panel_definitions
        ]

    @property
    def prefix(self):
        return self.form.prefix

    def is_being_deleted(self):
        if not self.can_delete:
            return False

        # largely snarfed from https://github.com/django/django/commit/08056572e8
        field = self.form.fields['DELETE']
        prefix = self.form.add_prefix('DELETE')
        value = field.widget.value_from_datadict(self.data, self.files, prefix)
        return field.clean(value)

    def is_valid(self):
        if self.is_being_deleted():
            # shortcut further validation if this model is going to be deleted anyway
            return True

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
        if self.is_being_deleted():
            return

        for panel in self.panels:
            panel.pre_save()

    def _post_save(self):
        if self.is_being_deleted():
            return

        for panel in self.panels:
            panel.post_save()

    def non_panel_fields(self):
        """
        return a list of fields that are in the form but not rendered by a panel
        """
        fields_rendered_by_panels = set()
        for panel in self.panels:
            for field in panel.rendered_fields():
                fields_rendered_by_panels.add(field)

        return [
            self.form[field_name] for field_name in self.form.fields if field_name not in fields_rendered_by_panels
        ]

    def render(self):
        return mark_safe(render_to_string("verdantadmin/panels/admin.html", {
            'admin': self
        }))

    def render_setup_js(self):
        """
        return a string of the JS code to be executed once the HTML has been rendered
        """
        return mark_safe(render_to_string("verdantadmin/panels/admin.js", {
            'admin': self
        }))
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
