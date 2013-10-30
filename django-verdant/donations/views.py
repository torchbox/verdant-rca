from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import DonationForm


def donation(request):
    if request.method == "GET":
        form = DonationForm()
    if request.method == "POST":
        form = DonationForm(request.POST)
        if form.is_valid():
            pass

    return render(request, 'donations/donation.html', {
        'form': form,
    })
