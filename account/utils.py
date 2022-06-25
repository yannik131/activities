import random

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
import logging
from redis import StrictRedis
import redis_lock
from geopy.extra.rate_limiter import RateLimiter
from django.apps import apps

geolocator = Nominatim(user_agent='activities')
logger = logging.getLogger('django')
conn = StrictRedis(host="localhost", port=6655)
_geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


def geocode(*args, **kwargs):
    with redis_lock.Lock(conn, 'geocode'):
        location = _geocode(*args, **kwargs)
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
    c.traits = {'ach': '10', 'act': '9', 'adv': '4', 'alt': '5', 'ang': '7', 'anx': '5', 'art': '7', 'ass': '7', 'cau': '9', 'che': '5', 'con': '6', 'coo': '8', 'dep': '8', 'dis': '8', 'dut': '9', 'eff': '5', 'emo': '9', 'exc': '5', 'fri': '6', 'gre': '8', 'ima': '9', 'imm': '8', 'int': '10', 'lib': '9', 'mod': '6', 'mor': '9', 'ord': '9', 'sym': '5', 'tru': '7', 'vul': '9'}
    c.current_question = 60
    c.question_limit = 60
    c.calculate_suggestions()
    c.save()

def generate_username():
    User = apps.get_model('account', 'User')
    while True:
        username = _('Gast') + str(random.randint(1, 1000000))
        if not User.objects.filter(username=username):
            return username
