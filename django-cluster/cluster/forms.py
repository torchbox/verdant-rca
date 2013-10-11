from django.forms.models import BaseModelFormSet, modelformset_factory, ModelForm, _get_foreign_key, ModelFormMetaclass
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


class BaseChildFormSet(BaseTransientModelFormSet):
    def __init__(self, data=None, files=None, instance=None, queryset=None, **kwargs):
        if instance is None:
            self.instance = self.fk.rel.to()
        else:
            self.instance=instance

        if queryset is None:
            self.rel_name = RelatedObject(self.fk.rel.to, self.model, self.fk).get_accessor_name()

            queryset = getattr(self.instance, self.rel_name).all()

        super(BaseChildFormSet, self).__init__(data, files, queryset=queryset, **kwargs)

    def save(self, commit=True):
        final_objects = []
        for form in self.initial_forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            else:
                final_objects.append(form.save(commit=False))

        for form in self.extra_forms:
            if not form.has_changed():
                continue
            elif self.can_delete and self._should_delete_form(form):
                continue
            else:
                final_objects.append(form.save(commit=False))


        setattr(self.instance, self.rel_name, final_objects)
        if commit:
            getattr(self.instance, self.rel_name).commit()
        return final_objects

def childformset_factory(parent_model, model, form=ModelForm,
    formset=BaseChildFormSet, fk_name=None, fields=None, exclude=None,
    extra=3, can_order=False, can_delete=True, max_num=None,
    formfield_callback=None):

    fk = _get_foreign_key(parent_model, model, fk_name=fk_name)
    # enforce a max_num=1 when the foreign key to the parent model is unique.
    if fk.unique:
        max_num = 1

    if exclude is None:
        exclude = []
    exclude += [fk.name]

    kwargs = {
        'form': form,
        'formfield_callback': formfield_callback,
        'formset': formset,
        'extra': extra,
        'can_delete': can_delete,
        'can_order': can_order,
        'fields': fields,
        'exclude': exclude,
        'max_num': max_num,
    }
    FormSet = modelformset_factory(model, **kwargs)
    FormSet.fk = fk
    return FormSet


class ClusterFormMetaclass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        try:
            parents = [b for b in bases if issubclass(b, ClusterForm)]
        except NameError:
            # We are defining ClusterForm itself.
            parents = None

        new_class = super(ClusterFormMetaclass, cls).__new__(cls, name, bases, attrs)
        if not parents:
            return new_class

        opts = new_class._meta
        if opts.model is None:
            raise ValueError('ModelForm has no model class specified.')

        try:
            child_relations = opts.model._meta.child_relations
        except AttributeError:
            child_relations = []

        formsets = {}
        for rel in child_relations:
            # to build a childformset class from this relation, need to know
            # the base model (opts.model), the child model, and the fk_name from the child model to the base
            formset = childformset_factory(opts.model, rel.model, fk_name=rel.field.name)
            formsets[rel.get_accessor_name()] = formset

        new_class.formsets = formsets

        return new_class

class ClusterForm(ModelForm):
    __metaclass__ = ClusterFormMetaclass

    def __init__(self, data=None, files=None, instance=None, prefix=None, **kwargs):
        super(ClusterForm, self).__init__(data, files, instance=instance, prefix=prefix, **kwargs)

        self.formsets = {}
        for rel_name, formset_class in self.__class__.formsets.items():
            if prefix:
                formset_prefix = "%s-%s" % (prefix, rel_name)
            else:
                formset_prefix = rel_name
            self.formsets[rel_name] = formset_class(data, files, instance=instance, prefix=formset_prefix)

    def as_p(self):
        form_as_p = super(ClusterForm, self).as_p()
        return form_as_p + u''.join([formset.as_p() for formset in self.formsets.values()])

    def is_valid(self):
        form_is_valid = super(ClusterForm, self).is_valid()
        formsets_are_valid = all([formset.is_valid() for formset in self.formsets.values()])
        return form_is_valid and formsets_are_valid

    def save(self, commit=True):
        result = super(ClusterForm, self).save(commit=commit)
        for formset in self.formsets.values():
            formset.save(commit=commit)
        return result
