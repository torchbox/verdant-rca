from django.shortcuts import render
from django.contrib.auth.models import User

def index(request):
    users = User.objects.all()

    return render(request, 'verdantusers/index.html', {
        'users': users,
    })

def logintest(request):
    return render(request, 'verdantusers/users/login.html', {})