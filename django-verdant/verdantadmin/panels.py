# a Panel is a vertical section of the admin add/edit page, responsible for editing
# some fields (or inline formsets) of the model.

from django import forms
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

        class FieldPanelInstance(AdminPanelInstance):
            def __init__(self, *args, **kwargs):
                super(FieldPanelInstance, self).__init__(*args, **kwargs)

            template = "verdantadmin/panels/field_panel.html"

            def render(self):
                return mark_safe(render_to_string(self.template, {'field': self.form[field_name]}))

            # TEMP - to check that javascript is being correctly applied to fields
            def render_js(self):
                return "$(fixPrefix('#%s')).click(function() {$(this).css('background-color', '#ddf')});" % self.form[field_name].id_for_label

            def rendered_fields(self):
                """return a list of names of fields that will be rendered by this panel"""
                return [field_name]

        self.panel_class = FieldPanelInstance

    def get_panel_instance(self, *args, **kwargs):
        return self.panel_class(*args, **kwargs)


class InlinePanel(object):
    def __init__(self, base_model, related_model, panels=None):
        formset_class = inlineformset_factory(base_model, related_model, extra=0)
        admin_handler_panels = panels

        # construct an AdminHandler class around the particular flavour of ModelForm
        # that inlineformset_factory generates
        from verdantadmin.forms import AdminHandler
        class InlineAdminHandler(AdminHandler):
            form = formset_class.form
            can_delete = True

            if admin_handler_panels is not None:
                panels = admin_handler_panels

        admin_handler = InlineAdminHandler

        class InlinePanelInstance(AdminPanelInstance):
            def __init__(self, *args, **kwargs):
                super(InlinePanelInstance, self).__init__(*args, **kwargs)
                self.formset = formset_class(*args, instance=self.model_instance)

                self.admin_handler_instances = []
                for form in self.formset.forms:
                    # override the DELETE field to have a hidden input
                    form.fields['DELETE'].widget = forms.HiddenInput()
                    self.admin_handler_instances.append(admin_handler(*args, form=form))

                empty_form = self.formset.empty_form
                empty_form.fields['DELETE'].widget = forms.HiddenInput()
                self.empty_form_admin_handler_instance = admin_handler(*args, form=empty_form)

            def render(self):
                return mark_safe(render_to_string("verdantadmin/panels/inline_panel.html", {
                    'admins': self.admin_handler_instances,
                    'empty_form_admin': self.empty_form_admin_handler_instance,
                    'formset': self.formset,
                }))

            def render_js(self):
                return mark_safe(render_to_string("verdantadmin/panels/inline_panel.js", {
                    'admins': self.admin_handler_instances,
                    'empty_form_admin': self.empty_form_admin_handler_instance,
                    'formset': self.formset,
                }))

            def is_valid(self):
                result = self.formset.is_valid()

                for admin in self.admin_handler_instances:
                    result &= admin.is_valid()

                return result

            def pre_save(self):
                for admin in self.admin_handler_instances:
                    admin._pre_save()

            def post_save(self):
                # inline relations need to be saved after the form is saved
                self.formset.save()

                # now we can run any post_save handlers on the child adminhandlers
                for admin in self.admin_handler_instances:
                    admin._post_save()

        self.panel_class = InlinePanelInstance

    def get_panel_instance(self, *args, **kwargs):
        return self.panel_class(*args, **kwargs)
