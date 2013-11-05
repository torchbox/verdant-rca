import simplejson
import stripe
import datetime

from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import DonationForm
from .settings import STRIPE_PUBLISHABLE_KEY, STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY


def unique(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x):
            return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result


def donation(request):
    if request.method == "GET":
        form = DonationForm()
    if request.method == "POST":
        form = DonationForm(request.POST)
        if form.is_valid():
            try:
                # When exporting the payments from the dashboard
                # the metadata field is not exported but the description is,
                # so we duplicate the metadata there as well.
                charge = stripe.Charge.create(
                    card=form.cleaned_data.get('stripe_token'),
                    amount=form.cleaned_data.get('amount'),  # amount in cents (converted by the form)
                    currency="gbp",
                    description=simplejson.dumps(form.cleaned_data.get('metadata', {})),
                    metadata=form.cleaned_data.get('metadata', {}),
                )
                messages.success(request, "OK")
            except stripe.CardError, e:
                # CardErrors are displayed to the user
                messages.error(request, e['message'])
            # TODO: for other exceptions we should send emails to admins and display a user freindly error message
            # InvalidRequestError (if token is used more than once) , AuthenticationError, APIError
            # except Exception, e:
            #     mail_admins()
            #     messages.error(request, "")

    return render(request, 'donations/donation.html', {
        'form': form,
        'STRIPE_PUBLISHABLE_KEY': STRIPE_PUBLISHABLE_KEY,
    })


def export(request):
    # TODO: parse dates from query params
    offset = request.POST.get("offset", 0)
    count = request.POST.get("count", 100)
    date_from = request.POST.get("date_from", datetime.datetime.now() - datetime.timedelta(days=31))
    date_to = request.POST.get("date_to", datetime.datetime.now())
    created = {
        "gte": date_from.strftime("%s"),
        "lte": date_to.strftime("%s"),
    }

    all_charges = []
    charges_left = True

    while charges_left:
        # https://stripe.com/docs/api/python#list_charges
        charges = stripe.Charge.all(count=count, offset=offset, created=created)['data']
        if len(charges):
            all_charges += charges
            offset = offset + count
        else:
            charges_left = False

    # if there was a charge made while retrieving the results there might be duplicates in the list
    all_charges = unique(all_charges, lambda c: c["id"])

    # covert objects to dicts, the ordering of keys and values is fixed:
    # http://docs.python.org/2/library/stdtypes.html#dict.items
    all_charges = [dict(zip(ch.keys(), ch.values())) for ch in all_charges]

    # TODO: flatten json and convert to csv
    return HttpResponse(simplejson.dumps(all_charges))
