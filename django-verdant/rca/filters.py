import json


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


def run_school_programme_filters(queryset, school, programme, school_field='school', programme_field='programme'):
    return run_filters(queryset, [
        ('school', school_field, school),
        ('programme', programme_field, programme),
    ])