import json


def run_school_programme_filters(queryset, school, programme, school_field='school', programme_field='programme'):
    # Get list of related schools
    related_schools = [
        values[school_field]
        for values in queryset.order_by(school_field).distinct(school_field).values(school_field)
    ]

    # Apply school filter
    if school:
        # See below comment for explanation
        queryset_school = queryset.filter(**{school_field: school})

        if queryset_school.exists():
            queryset = queryset_school
        else:
            school = None

    # Get list of related programmes
    related_programmes = [
        values[programme_field]
        for values in queryset.order_by(programme_field).distinct(programme_field).values(programme_field)
    ]

    # Apply programme filter
    if programme:
        # Only apply programme filter if there are items this programme
        # Reason: If a programme is chosen, and the user changes to a different school,
        # there may be no results displayed (as the programme might not exist in the new school).
        # This check automatically unsets the programme in this case.
        queryset_programme = queryset.filter(**{programme_field: programme})

        if queryset_programme.exists():
            queryset = queryset_programme
        else:
            programme = None

    # This dictionay needs to become a javascript variable called "filters_context".
    # It gets used inside the filters.js file
    filters_context = json.dumps({
        'selected_school': school if school else '',
        'selected_programme': programme if programme else '',
        'related_schools': related_schools,
        'related_programmes': related_programmes,
    })

    return queryset, filters_context