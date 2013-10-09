from django.forms.models import BaseModelFormSet, BaseInlineFormSet, modelformset_factory, inlineformset_factory
from django.db.models.fields.related import RelatedObject


class BaseTransientModelFormSet(BaseModelFormSet):
    """ A ModelFormSet that doesn't assume that all its initial data instances exist in the db """
    def _construct_form(self, i, **kwargs):
        if self.is_bound and i < self.initial_form_count():
            kwargs['instance'] = self.model()
        elif i < self.initial_form_count():
            kwargs['instance'] = self.get_queryset()[i]
        elif self.initial_extra:
            # Set initial values for extra forms
            try:
                kwargs['initial'] = self.initial_extra[i-self.initial_form_count()]
            except IndexError:
                pass

        # bypass BaseModelFormSet's own _construct_form
        return super(BaseModelFormSet, self)._construct_form(i, **kwargs)

def transientmodelformset_factory(model, formset=BaseTransientModelFormSet, **kwargs):
    return modelformset_factory(model, formset=formset, **kwargs)


class BaseChildFormSet(BaseInlineFormSet):
    def __init__(self, data=None, files=None, instance=None, queryset=None, **kwargs):

        if queryset is None and instance is not None:
            rel_name = RelatedObject(self.fk.rel.to, self.model, self.fk).get_accessor_name()
            queryset = getattr(instance, rel_name).all()

        super(BaseChildFormSet, self).__init__(data, files, instance=instance,
            queryset=queryset, **kwargs)

def childformset_factory(parent_model, model, formset=BaseChildFormSet, **kwargs):
    return inlineformset_factory(parent_model, model, formset=formset, **kwargs)
