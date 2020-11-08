from .base import *

DEBUG = True

ALLOWED_HOSTS = ['mysite.com', 'en.mysite.com', 'de.mysite.com', 'localhost']

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
