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
            }
            for school in School.objects.all()
        },
        'programmes': {
            graduation_year: {
                programme.slug: {
                    'display_name': programme.display_name,
                    'school': programme.school.slug,
                }
                for programme in Programme.objects.filter(graduation_year=graduation_year).select_related('school__slug')
            }
            for graduation_year in Programme.objects.order_by('-graduation_year').values_list('graduation_year', flat=True).distinct('graduation_year')
        }
    })
