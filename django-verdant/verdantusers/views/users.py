from django.shortcuts import render

def logintest(request):
    return render(request, 'verdantusers/users/login.html', {})