import simplejson
import stripe

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import DonationForm
from .settings import STRIPE_PUBLISHABLE_KEY, STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY


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
