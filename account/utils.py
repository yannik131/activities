from shared.shared import log
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
import logging
logger = logging.getLogger('django')


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
    
def send_mail(subject, msg=""):
    try:
        email = EmailMultiAlternatives(subject, msg, 'myactivities.net@web.de', ['yannik131@web.de'])
        email.send()
    except:
        logging.log(logging.ERROR, 'Could not send email', exc_info=True)
    
    
def test(func, n=100):
    stamp = timer()
    for i in range(n):
        func()
    print((timer()-stamp)/10**6)
    

def set_result(user):
    c = user.character
    c.traits = {'ach': '10', 'act': '7', 'adv': '4', 'alt': '5', 'ang': '7', 'anx': '5', 'art': '7', 'ass': '7', 'cau': '9', 'che': '5', 'con': '6', 'coo': '8', 'dep': '8', 'dis': '8', 'dut': '9', 'eff': '5', 'emo': '7', 'exc': '5', 'fri': '6', 'gre': '7', 'ima': '9', 'imm': '6', 'int': '10', 'lib': '9', 'mod': '6', 'mor': '9', 'ord': '9', 'sym': '5', 'tru': '7', 'vul': '9'}
    c.current_question = 60
    c.question_limit = 60
    c.calculate_suggestions()
    c.save()
