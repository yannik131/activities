from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '192.168.0.26']

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
