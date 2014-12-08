from collections import OrderedDict
from decimal import Decimal
from datetime import date, datetime, timedelta
import csv
import simplejson
import stripe

from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from donations.forms import DonationForm
from donations.mail_admins import mail_exception
from django.conf import settings
from donations.csv_unicode import UnicodeWriter
from django.contrib.auth.decorators import permission_required

# stripe.api_key = settings.STRIPE_SECRET_KEY

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


@permission_required('donations.download_donations')
def export(request, include_all=False):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    def unique(seq, idfun=None):
        # order preserving
        if idfun is None:
            def idfun(x):
                return x
        seen = {}
        result = []
        for item in seq:
            marker = idfun(item)
            if marker in seen:
                continue
            seen[marker] = 1
            result.append(item)
        return result

    offset = request.REQUEST.get("offset", 0)
    delimiter = request.REQUEST.get("delimiter", ",")
    count = request.REQUEST.get("count", 100)
    date_from = request.REQUEST.get("date_from")
    date_to = request.REQUEST.get("date_to")

    # parse dates or use the current day by default
    date_from = date.today() if not date_from else datetime.strptime(date_from, '%Y-%m-%d').date()
    date_to = date.today() if not date_to else datetime.strptime(date_to, '%Y-%m-%d').date()

    # and add one day to date_to so that it covers the whole day when converted to seconds
    created = {
        "gte": date_from.strftime("%s"),
        "lte": (date_to + timedelta(days=1)).strftime("%s"),
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

        if charge.get('metadata__is_gift_aid') and charge.get('metadata__is_gift_aid') != "False":
            # add 20% giftaid field, with two decimal places:
            # http://docs.python.org/2/library/decimal.html#decimal-faq
            charge['amount_gift_aid'] = (charge['amount'] * Decimal(0.2)).quantize(Decimal(10) ** -2)
        else:
            charge['amount_gift_aid'] = 0

        charge.get('metadata__is_gift_aid', False)

        charge['created'] = datetime.fromtimestamp(int(charge['created'])).strftime('%Y-%m-%d %H:%M:%S')

        phone = charge.get('metadata__phone')
        if phone:
            charge['metadata__phone'] = phone[:5] + " " + phone[5:]

        fieldnames |= set(charge.keys())

    _fieldnames = sorted(list(fieldnames))

    headers = OrderedDict((
        ("id", "Transaction identifier"),
        ("created", "Date created"),
        ("description", "Description (set in page admin ui in Verdant)"),
        ("amount", "Donation amount"),
        ("amount_gift_aid", "Giftaid amount"),
        ("metadata__is_gift_aid", "Gift aid donation"),
        ("metadata__not_included_in_supporters_list", "NOT included in supporters list"),
        ("metadata__title", "Title"),
        ("metadata__first_name", "First name"),
        ("metadata__last_name", "Last name"),
        ("metadata__email", "Email"),
        ("metadata__phone", "Phone number"),
        ("metadata__class_year", "Class year"),
        ("metadata__donation_for", "Gift directed to"),
        ("metadata__affiliation", "Affiliation"),
        ("card__address_city", "City"),
        ("card__address_country", "Country"),
        ("card__address_line1", "Address line 1"),
        ("card__address_line2", "Address line 2"),
        ("card__address_state", "State / Province"),
        ("card__address_country", "Country"),
        ("card__address_zip", "ZIP / Postal code"),
        # "metadata__phone_type": "Phone type",
    ))

    fieldnames = [str(f) for f in _fieldnames if str(f) in headers.keys()]

    def key(f):
        return headers.keys().index(f)

    fieldnames = sorted(fieldnames, key=key)

    # create response
    response = HttpResponse(content_type='text/csv')
    filename = 'rca-donations-%s--%s.csv' % (date_from.strftime("%Y-%m-%d"), date_to.strftime("%Y-%m-%d"))
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    # write header
    writer = UnicodeWriter(response, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow([headers[f] for f in fieldnames])

    # write data rows
    for charge in all_charges:
        if not include_all:
            if not charge.get('amount_gift_aid') or not charge['paid'] or charge['refunded']:
                continue
        data = [unicode(charge[f] if f in charge else '') for f in fieldnames]
        writer.writerow(data)

    return response


@permission_required('donations.download_donations')
def wagtailadmin(request, title=None):
    return render(request, 'donations/wagtailadmin.html', {})
