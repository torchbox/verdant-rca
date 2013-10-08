from django.forms.models import BaseInlineFormSet, inlineformset_factory
from django.db.models.fields.related import RelatedObject

class BaseChildFormSet(BaseInlineFormSet):
    def __init__(self, data=None, files=None, instance=None, queryset=None, **kwargs):

        if queryset is None and instance is not None:
            rel_name = RelatedObject(self.fk.rel.to, self.model, self.fk).get_accessor_name()
            queryset = getattr(instance, rel_name).all()

        super(BaseChildFormSet, self).__init__(data, files, instance=instance,
            queryset=queryset, **kwargs)

def childformset_factory(parent_model, model, formset=BaseChildFormSet, **kwargs):
    return inlineformset_factory(parent_model, model, formset=formset, **kwargs)
