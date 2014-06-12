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
    If the year does not exist, this function will return None
    """
    school_programme_map = get_school_programme_map(year)
    if not school_programme_map:
        return

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


def get_students(ma=True, mphil=True, phd=True, degree_filters={}):
    # Get list of degrees
    degrees = []
    if ma:    degrees.append('ma')
    if mphil: degrees.append('mphil')
    if phd:   degrees.append('phd')

    if not degrees:
        return NewStudentPage.objects.none()

    # Build a Q object
    q = Q()
    for degree in degrees:
        q |= Q(**{
            degree + '_' + filter_name: filter_value
            for filter_name, filter_value in degree_filters.items()
        })

    return NewStudentPage.objects.live().filter(q)
