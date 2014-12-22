from django import forms
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .forms import ProfileBasicForm, EmailFormset, PhoneFormset, WebsiteFormset



    
@login_required
def basic_profile(request):
    data = {}
    
    data['basic_form'] = ProfileBasicForm()
    data['email_formset'] = EmailFormset(prefix='email')
    data['phone_formset'] = PhoneFormset(prefix='phone')
    data['website_formset'] = WebsiteFormset(prefix='website')

    if request.method == 'POST':
        data['basic_form'] = basic_form = ProfileBasicForm(request.POST, request.FILES)
        data['email_formset'] = email_formset = EmailFormset(request.POST, prefix='email')
        data['phone_formset'] = phone_formset = PhoneFormset(request.POST, prefix='phone')
        data['website_formset'] = website_formset = WebsiteFormset(request.POST, prefix='website')
        if basic_form.is_valid() and email_formset.is_valid() and phone_formset.is_valid() and website_formset.is_valid():
            print(basic_form.cleaned_data)
            print(email_formset.cleaned_data)
            print(phone_formset.cleaned_data)
            print(website_formset.cleaned_data)
        else:
            print("something is invalid")
            print("basic:", basic_form.is_valid())
            print("email:", email_formset.is_valid())
            print("phone:", phone_formset.is_valid())
            print("website:", website_formset.is_valid())
    
    return render(request, 'student_profiles/basic.html', data)
