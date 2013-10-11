from django.db import models


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

    class Meta:
        abstract = True