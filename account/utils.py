from geopy import Nominatim
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import translation
from time import perf_counter_ns as timer
import time
geolocator = Nominatim(user_agent='activities')

def geocode(*args, **kwargs):
    location = geolocator.geocode(*args, **kwargs)
    time.sleep(1)
    return location
        

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