from .base import *

DEBUG = False

ALLOWED_HOSTS = ['myactivities.net', 'www.myactivities.net', 'de.myactivities.net', 'en.myactivities.net']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'activities',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
