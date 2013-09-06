# a Panel is a vertical section of the admin add/edit page, responsible for editing
# some fields (or inline formsets) of the model.

from django.forms import HiddenInput
from django.forms.models import inlineformset_factory
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class BaseAdminPanel(object):
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


# Abstract superclass of FieldPanel types. Subclasses need to provide a field_name attribute.
class BaseFieldPanel(BaseAdminPanel):
    template = "verdantadmin/panels/field_panel.html"

    def render(self):
        return mark_safe(render_to_string(self.template, {'field': self.form[self.field_name]}))

    # TEMP - to check that javascript is being correctly applied to fields
    def render_js(self):
        return "$(fixPrefix('#%s')).click(function() {$(this).css('background-color', '#ddf')});" % self.form[self.field_name].id_for_label

    def rendered_fields(self):
        """return a list of names of fields that will be rendered by this panel"""
        return [self.field_name]

def FieldPanel(field_name):
    # return a newly constructed subclass of BaseFieldPanel whose only difference
    # is the addition of a self.field_name attribute
    return type('_FieldPanel', (BaseFieldPanel,), {'field_name': field_name})


# Abstract superclass of InlinePanel types. Subclasses need to provide:
# - a formset class (self.formset_class)
# - an admin handler class (self.admin_handler)
# (TODO: construct these things using a metaclass when BaseInlinePanel is subclassed,
# meaning that subclasses only have to provide base_model, related_model and an
# optional panels list)

class BaseInlinePanel(BaseAdminPanel):
    def __init__(self, *args, **kwargs):
        super(BaseInlinePanel, self).__init__(*args, **kwargs)
        self.formset = self.formset_class(*args, instance=self.model_instance)

        self.admin_handler_instances = []
        for form in self.formset.forms:
            # override the DELETE field to have a hidden input
            form.fields['DELETE'].widget = HiddenInput()
            self.admin_handler_instances.append(self.admin_handler(*args, form=form))

        empty_form = self.formset.empty_form
        empty_form.fields['DELETE'].widget = HiddenInput()
        self.empty_form_admin_handler_instance = self.admin_handler(*args, form=empty_form)

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

        # NB we avoid calling save() on the admin handler instances
        # because this will cause their forms to be saved; we don't
        # want to do this as formset.save() handles this for us, with some
        # nuances (e.g. not saving deleted fields).

        # now we can run any post_save handlers on the child adminhandlers
        for admin in self.admin_handler_instances:
            admin._post_save()

def InlinePanel(base_model, related_model, panels=None):
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

    # return a newly constructed subclass of BaseInlinePanel with the addition of
    # a self.formset_class and self.admin_handler attribute
    return type('_InlinePanel', (BaseInlinePanel,), {
        'formset_class': formset_class,
        'admin_handler': InlineAdminHandler
    })
