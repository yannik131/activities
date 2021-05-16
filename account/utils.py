from .models import Location
from geopy import Nominatim
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import translation
from time import perf_counter_ns as timer


def get_location(address):
    try:
        location = Location.objects.get(city=address)
        return location
    except Location.DoesNotExist:
        pass
    geolocator = Nominatim(user_agent='activities')
    location = geolocator.geocode(address, addressdetails=True)
    if location is None:
        raise ValidationError(_('Diese Adresse konnte nicht gefunden werden.'))
    elif location.raw['address'].get('city', location.raw['address'].get('town')) is None:
        raise ValidationError(_('Aus der Adresse konnte die Stadt nicht ermittelt werden. Bitte geben Sie die Stadt explizit an (Dörfer/Ortsteile werden nicht erkannt).'))
    else:
        return Location.get_from_location(location)
        

def send_account_activation_email(request, user):
    recipients = [user.email]
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_url = request.build_absolute_uri(f'/account/activate/{uidb64}/{token}/')
    with translation.override(request.LANGUAGE_CODE):
        html_content = render_to_string('registration/activation_email.html', dict(user=user, activation_url=activation_url, LANGUAGE_CODE=request.LANGUAGE_CODE))
    email = EmailMultiAlternatives(_('E-Mail Aktivierung'), _('Aktivierungs-E-Mail'), settings.DEFAULT_FROM_EMAIL, recipients)
    email.attach_alternative(html_content, 'text/html')
    email.send()
    
def test(func, n=100):
    stamp = timer()
    for i in range(n):
        func()
    print((timer()-stamp)/10**6)