from django.db.models import Q

from .models import SCHOOL_PROGRAMME_MAP, NewStudentPage

def get_school_programme_map(year=None):
    """
    This function gets a mapping of schools to programmes for a particular year

    If the year is unspecified, then the latest year in the SCHOOL_PROGRAMME_MAP will be used
    """
    if year:
        if year in SCHOOL_PROGRAMME_MAP:
            return SCHOOL_PROGRAMME_MAP[year]
        else:
            return
    else:
        return SCHOOL_PROGRAMME_MAP[max(SCHOOL_PROGRAMME_MAP.keys())]


def get_schools(year=None):
    """
    This function gets a list of school slugs for the specified school/year

    If year is unspecified, the latest year in the SCHOOL_PROGRAMME_MAP will be used
    If the year does not exist, this function will return an empty list
    """
    school_programme_map = get_school_programme_map(year)
    if not school_programme_map:
        return []

    return school_programme_map.keys()


def get_programmes(school=None, year=None):
    """
    This function gets a list of programme slugs for the specified school/year

    If the school is unspecified, all programmes for the year will be returned
    If year is unspecified, the latest year in the SCHOOL_PROGRAMME_MAP will be used
    If the school or year does not exist, this function will return None
    """
    school_programme_map = get_school_programme_map(year)
    if not school_programme_map:
        return

    if school:
        if school in school_programme_map:
            return school_programme_map[school]
        else:
            return
    else:
        programmes = []
        for extra_programmes in school_programme_map.values():
            programmes.extend(extra_programmes)
        return list(set(programmes))


def get_school_for_programme(programme, year=None):
    """
    This function takes a programme slug and returns the school slug that the programme is in

    If year is unspecified, the latest year in the SCHOOL_PROGRAMME_MAP will be used
    If the programme or year does not exist, this function will return None
    """
    school_programme_map = get_school_programme_map(year)
    if not school_programme_map:
        return

    for school, programmes in school_programme_map.items():
        if programme in programmes:
            return school


def convert_degree_filters(q, degree):
    if isinstance(q, tuple):
        fil, arg = q

        if degree == 'ma' and fil.startswith('carousel_items'):
            fil = 'show_' + fil
        else:
            fil = degree + '_' + fil

        return fil, arg
    else:
        new_q = q.__class__._new_instance(
            children=[], connector=q.connector, negated=q.negated)

        for child_q in q.children:
            new_q.children.append(convert_degree_filters(child_q, degree))

        return new_q


def get_students(ma=True, mphil=True, phd=True, degree_filters=None, degree_q=None):
    # Make sure one degree was set
    if not ma or not mphil or not phd:
        return NewStudentPage.objects.none()

    # Get degree_q
    if degree_q is None:
        degree_q = Q()

    # Build a Q object from degree_filters
    if degree_filters is not None:
        degree_q &= Q(**degree_filters)

    # Rewrite Q object to use actual field names
    final_q = Q()
    if ma:
        final_q |= convert_degree_filters(degree_q, 'ma')

    if mphil:
        final_q |= convert_degree_filters(degree_q, 'mphil')

    if phd:
        final_q |= convert_degree_filters(degree_q, 'phd')

    return NewStudentPage.objects.live().filter(final_q)
