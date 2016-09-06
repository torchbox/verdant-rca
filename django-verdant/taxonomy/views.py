from django.http import JsonResponse

from .models import Area, School, Programme


def api(request):
    return JsonResponse({
        'areas': {
            area.slug: {
                'display_name': area.display_name,
            }
            for area in Area.objects.all()
        },
        'schools': {
            school.slug: {
                'display_name': school.display_name,
                'historical_display_names': {
                    hdn.end_year: hdn.display_name
                    for hdn in school.historical_display_names.all()
                }
            }
            for school in School.objects.all()
        },
        'programmes': {
            programme.slug: {
                'display_name': programme.display_name,
                'historical_display_names': {
                    hdn.end_year: hdn.display_name
                    for hdn in programme.historical_display_names.all()
                },
                'school': programme.school.slug,
                'disabled': programme.disabled,
            }
            for programme in Programme.objects.select_related('school__slug')
        }
    })
