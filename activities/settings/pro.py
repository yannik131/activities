from .base import *

DEBUG = True

ADMINS = (
    ('Yannik S.', 'yannik131@web.de'),
)

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
