from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm


def account(request):
    return render(request, 'verdantadmin/account/account.html')


def change_password(request):
    if request.POST:
        form = SetPasswordForm(request.user, request.POST)

        if form.is_valid():
            form.save()

            messages.success(request, "Your password has been changed successfully!")
            return redirect('verdantadmin_account')
    else:
        form = SetPasswordForm(request.user)
    return render(request, 'verdantadmin/account/change_password.html', {
        'form': form,
    })