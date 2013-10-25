from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils.encoding import is_protected_type
from django.core.serializers.json import DjangoJSONEncoder

import json


def get_field_value(field, model):
    if field.rel is None:
        value = field._get_val_from_obj(model)
        if is_protected_type(value):
            return value
        else:
            return field.value_to_string(model)
    else:
        return getattr(model, field.get_attname())

def get_serializable_data_for_fields(model):
    pk_field = model._meta.pk
    # If model is a child via multitable inheritance, use parent's pk
    while pk_field.rel and pk_field.rel.parent_link:
        pk_field = pk_field.rel.to._meta.pk

    obj = {'pk': get_field_value(pk_field, model)}

    for field in model._meta.fields:
        if field.serialize:
            obj[field.name] = get_field_value(field, model)

    return obj

def model_from_serializable_data(model, data):
    pk_field = model._meta.pk
    # If model is a child via multitable inheritance, use parent's pk
    while pk_field.rel and pk_field.rel.parent_link:
        pk_field = pk_field.rel.to._meta.pk

    kwargs = {pk_field.attname: data['pk']}
    for field_name, field_value in data.iteritems():
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            continue

        if field.rel and isinstance(field.rel, models.ManyToManyRel):
            raise Exception('m2m relations not supported yet')
        elif field.rel and isinstance(field.rel, models.ManyToOneRel):
            if field_value is None:
                kwargs[field.attname] = None
            else:
                kwargs[field.attname] = field.rel.to._meta.get_field(field.rel.field_name).to_python(field_value)
        else:
            kwargs[field.name] = field.to_python(field_value)

    return model(**kwargs)


class ClusterableModel(models.Model):
    def __init__(self, *args, **kwargs):
        """
        Extend the standard model constructor to allow child object lists to be passed in
        via kwargs
        """
        try:
            child_relation_names = [rel.get_accessor_name() for rel in self._meta.child_relations]
        except AttributeError:
            child_relation_names = []

        is_passing_child_relations = False
        for rel_name in child_relation_names:
            if rel_name in kwargs:
                is_passing_child_relations = True
                break

        if is_passing_child_relations:
            kwargs_for_super = kwargs.copy()
            relation_assignments = {}
            for rel_name in child_relation_names:
                if rel_name in kwargs:
                    relation_assignments[rel_name] = kwargs_for_super.pop(rel_name)

            super(ClusterableModel, self).__init__(*args, **kwargs_for_super)
            for (field_name, related_instances) in relation_assignments.items():
                setattr(self, field_name, related_instances)
        else:
            super(ClusterableModel, self).__init__(*args, **kwargs)

    def save(self, **kwargs):
        """
        Save the model and commit all child relations.
        """
        try:
            child_relation_names = [rel.get_accessor_name() for rel in self._meta.child_relations]
        except AttributeError:
            child_relation_names = []

        update_fields = kwargs.pop('update_fields', None)
        if update_fields is None:
            real_update_fields = None
            relations_to_commit = child_relation_names
        else:
            real_update_fields = []
            relations_to_commit = []
            for field in update_fields:
                if field in child_relation_names:
                    relations_to_commit.append(field)
                else:
                    real_update_fields.append(field)

        super(ClusterableModel, self).save(update_fields=real_update_fields, **kwargs)

        for relation in relations_to_commit:
            getattr(self, relation).commit()

    def serializable_data(self):
        obj = get_serializable_data_for_fields(self)

        try:
            child_relations = self._meta.child_relations
        except AttributeError:
            child_relations = []

        for rel in child_relations:
            rel_name = rel.get_accessor_name()
            children = getattr(self, rel_name).all()

            if hasattr(rel.model, 'serializable_data'):
                obj[rel_name] = [child.serializable_data() for child in children]
            else:
                obj[rel_name] = [get_serializable_data_for_fields(child) for child in children]

        return obj

    def to_json(self):
        return json.dumps(self.serializable_data(), cls=DjangoJSONEncoder)

    @classmethod
    def from_serializable_data(cls, data):
        obj = model_from_serializable_data(cls, data)

        try:
            child_relations = cls._meta.child_relations
        except AttributeError:
            child_relations = []

        for rel in child_relations:
            rel_name = rel.get_accessor_name()
            try:
                child_data_list = data[rel_name]
            except KeyError:
                continue

            if hasattr(rel.model, 'from_serializable_data'):
                children = [rel.model.from_serializable_data(child_data) for child_data in child_data_list]
            else:
                children = [model_from_serializable_data(rel.model, child_data) for child_data in child_data_list]

            setattr(obj, rel_name, children)

        return obj

    @classmethod
    def from_json(cls, json_data):
        return cls.from_serializable_data(json.loads(json_data))

    class Meta:
        abstract = True