from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

def index(request):
    users = User.objects.all()

    return render(request, 'verdantusers/index.html', {
        'users': users,
    })

def create(request):
    if request.POST:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "User '%s' created." % user)
            return redirect('verdantusers_index')
    else:
        form = UserCreationForm()

    return render(request, 'verdantusers/create.html', {
        'form': form
    })

def logintest(request):
    return render(request, 'verdantusers/users/login.html', {})