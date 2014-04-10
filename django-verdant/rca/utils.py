from .models import SCHOOL_PROGRAMME_MAP

def get_school_programme_map(year=None):
    if year:
        return SCHOOL_PROGRAMME_MAP[year]
    else:
        return SCHOOL_PROGRAMME_MAP[max(SCHOOL_PROGRAMME_MAP.keys())]


def get_programmes_for_school(school, year=None):
    school_programme_map = get_school_programme_map(year)

    return school_programme_map[school]


def get_school_for_programme(programme, year=None):
    school_programme_map = get_school_programme_map(year)

    for school, programmes in school_programme_map.items():
        if programme in programmes:
            return school
