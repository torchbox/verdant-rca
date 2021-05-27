from django.shortcuts import render

from rca.models import NewStudentPageQuerySet, NewStudentPage


def rca_show(request):
    students = NewStudentPageQuerySet(NewStudentPage).live()
    return render(request, 'rca/archive_it.html', {
        'count': students.count(),
        'pages': students.order_by('first_name', 'last_name')
    })
