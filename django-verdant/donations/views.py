import datetime
import csv
import simplejson
import stripe
from decimal import Decimal

from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from donations.forms import DonationForm
from django.conf import settings
from donations.csv_unicode import UnicodeWriter


stripe.api_key = settings.STRIPE_SECRET_KEY


# def donation(request):
#     if request.method == "GET":
#         form = DonationForm()
#     if request.method == "POST":
#         form = DonationForm(request.POST)
#         if form.is_valid():
#             try:
#                 # When exporting the payments from the dashboard
#                 # the metadata field is not exported but the description is,
#                 # so we duplicate the metadata there as well.
#                 charge = stripe.Charge.create(
#                     card=form.cleaned_data.get('stripe_token'),
#                     amount=form.cleaned_data.get('amount'),  # amount in cents (converted by the form)
#                     currency="gbp",
#                     description=simplejson.dumps(form.cleaned_data.get('metadata', {})),
#                     metadata=form.cleaned_data.get('metadata', {}),
#                 )
#                 messages.success(request, "OK")
#             except stripe.CardError, e:
#                 # CardErrors are displayed to the user
#                 messages.error(request, e['message'])
#             # TODO: for other exceptions we should send emails to admins and display a user freindly error message
#             # InvalidRequestError (if token is used more than once) , AuthenticationError, APIError
#             # except Exception, e:
#             #     mail_admins()
#             #     messages.error(request, "")

#     return render(request, 'donations/donation.html', {
#         'form': form,
#         'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
#     })


def export(request):
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

    # TODO: parse dates from query params
    offset = request.POST.get("offset", 0)
    delimiter = request.POST.get("delimiter", ",")
    count = request.POST.get("count", 100)
    date_from = request.POST.get("date_from", datetime.datetime.now() - datetime.timedelta(days=1))
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

    # make sure we collect all the possible field names used in all charge objects
    fieldnames = set()

    # normalise data
    for charge in all_charges:

        # move metadata and card properties to charge objects, so that they can be separate columns
        for field in ['metadata', 'card']:
            if field in charge:
                for key, value in charge[field].items():
                    if not key.startswith("exp_"):  # skipping some credit card details
                        charge['%s__%s' % (field, key)] = value

        # remove unused fields
        for field in ['metadata', 'previous_metadata', 'card']:
            if field in charge:
                del charge[field]

        # convert amount from cents
        charge['amount'] = int(charge['amount']) / Decimal(100)

        # add 20% giftaid field, with two decimal places:
        # http://docs.python.org/2/library/decimal.html#decimal-faq
        charge['amount_gift_aid'] = (charge['amount'] * Decimal(0.2)).quantize(Decimal(10) ** -2)

        fieldnames |= set(charge.keys())

    fieldnames = sorted(list(fieldnames))

    # create response
    response = HttpResponse(content_type='text/csv')
    filename = 'rca-donations-%s--%s.csv' % (date_from.strftime("%Y-%m-%d-%H:%M"), date_to.strftime("%Y-%m-%d-%H:%M"))
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    # write header
    writer = UnicodeWriter(response, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(fieldnames)

    # write data rows
    for charge in all_charges:
        data = [unicode(charge[f] if f in charge else '') for f in fieldnames]
        writer.writerow(data)

    return response
