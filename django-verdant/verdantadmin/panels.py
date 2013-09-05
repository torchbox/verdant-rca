# a Panel is a vertical section of the admin add/edit page, responsible for editing
# some fields (or inline formsets) of the model.

from django.forms.models import inlineformset_factory
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class AdminPanelInstance(object):
    def __init__(self, *args, **kwargs):
        self.model_instance = kwargs['instance']
        self.form = kwargs['form']

    def is_valid(self):
        return True

    def pre_save(self):
        pass

    def post_save(self):
        pass

    def render(self):
        return ""

    def render_js(self):
        return ""

    def rendered_fields(self):
        """return a list of names of fields that will be rendered by this panel"""
        return []


class FieldPanel(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def get_panel_instance(self, *args, **kwargs):
        field_name = self.field_name

        # FIXME: defining this on every call to get_panel_instance is sucky. METACLASS VOODOO AHOY!
        class FieldPanelInstance(AdminPanelInstance):
            def __init__(self, *args, **kwargs):
                super(FieldPanelInstance, self).__init__(*args, **kwargs)

            template = "verdantadmin/panels/field_panel.html"

            def render(self):
                return mark_safe(render_to_string(self.template, {'field': self.form[field_name]}))

            def rendered_fields(self):
                """return a list of names of fields that will be rendered by this panel"""
                return [field_name]

        return FieldPanelInstance(*args, **kwargs)


class InlinePanel(object):
    def __init__(self, base_model, related_model, panels=None):
        formset_class = inlineformset_factory(base_model, related_model, extra=0)
        self.formset_class = formset_class
        admin_handler_panels = panels

        # construct an AdminHandler class around the particular flavour of ModelForm
        # that inlineformset_factory generates
        from verdantadmin.forms import AdminHandler
        class InlineAdminHandler(AdminHandler):
            form = formset_class.form
            if admin_handler_panels is not None:
                panels = admin_handler_panels

        self.admin_handler = InlineAdminHandler

    def get_panel_instance(self, *args, **kwargs):
        formset_class = self.formset_class
        admin_handler = self.admin_handler

        class InlinePanelInstance(AdminPanelInstance):
            def __init__(self, *args, **kwargs):
                super(InlinePanelInstance, self).__init__(*args, **kwargs)
                self.formset = formset_class(*args, instance=self.model_instance)

                self.admin_handler_instances = [
                    admin_handler(*args, form=form)
                    for form in self.formset.forms
                ]

            def render(self):
                return mark_safe(render_to_string("verdantadmin/panels/inline_panel.html", {
                    'admins': self.admin_handler_instances,
                    'formset': self.formset
                }))

            def render_js(self):
                return mark_safe(render_to_string("verdantadmin/panels/inline_panel.js", {
                    'formset': self.formset
                }))

            def is_valid(self):
                return self.formset.is_valid()

            def post_save(self):
                # inline relations need to be saved after the form is saved
                self.formset.save()

        return InlinePanelInstance(*args, **kwargs)
