from django.db import models
from django.utils.encoding import is_protected_type

import json


def get_serializable_data_for_fields(model):
    obj = {'pk': model._get_pk_val()}

    for field in model._meta.fields:
        if field.serialize:
            if field.rel is None:
                value = field._get_val_from_obj(model)
                if is_protected_type(value):
                    obj[field.name] = value
                else:
                    obj[field.name] = field.value_to_string(model)
            else:
                value = getattr(model, field.get_attname())
                obj[field.name] = value

    return obj


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
        return json.dumps(self.serializable_data())

    class Meta:
        abstract = True