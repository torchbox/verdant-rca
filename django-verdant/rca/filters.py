from django.db.models import Q
import json


def run_filters_q(cls, q, filters):
    filters_out = []

    # Iterate through filters
    for name, field, current_value in filters:
        # Get queryset
        queryset = cls.objects.filter(q)

        # Get options
        options = [
            values[field]
            for values in queryset.order_by(field).distinct(field).values(field)
        ]

        # Apply filter to queryset
        if current_value:
            queryset_filtered = queryset.filter(**{field: current_value})

            # Only apply the filter if there are values
            if queryset_filtered.exists():
                q &= Q(**{field: current_value})
            else:
                current_value = None

        # Add filter to output
        filters_out.append(dict(name=name, current_value=current_value, options=options))

    return filters_out


def run_filters(queryset, filters):
    filters_out = []

    # Iterate through filters
    for name, field, current_value in filters:
        # Get options
        options = [
            values[field]
            for values in queryset.order_by(field).distinct(field).values(field)
        ]

        # Apply filter to queryset
        if current_value:
            queryset_filtered = queryset.filter(**{field: current_value})

            # Only apply the filter if there are values
            if queryset_filtered.exists():
                queryset = queryset_filtered
            else:
                current_value = None

        # Add filter to output
        filters_out.append(dict(name=name, current_value=current_value, options=options))

    return queryset, filters_out


def combine_filters(*args):
    fields = {}

    for the_filter in args:
        for field in the_filter:
            if field['name'] not in fields.keys():
                fields[field['name']] = {
                    'current_value': field['current_value'],
                    'options': field['options'],
                }
            else:
                fields[field['name']] = {
                    'current_value': fields[field['name']]['current_value'] or field['current_value'],
                    'options': list(set(fields[field['name']]['options'] + field['options'])),
                }

    return [
        {
            'name': name,
            'current_value': field['current_value'],
            'options': field['options'],
        }
        for name, field in fields.items()
    ]


def get_filters_q(filters, field_mapping):
    q = Q()

    for fil in filters:
        if fil['name'] in field_mapping and fil['current_value']:
            field = field_mapping[fil['name']]
            q &= Q(**{field: fil['current_value']})

    return q