"""
Django settings for activities project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

"""
To load the settings for one shell session, type
export DJANGO_SETTINGS_MODULE=activities.settings.local_linux
Add this line to .bashrc or .bash_profile to have it executed automatically upon shell launch.
There is also a flag: ./manage.py command --settings=activities.settings.local_linux
In case of pkey integrity error, run
python3 manage.py sqlsequencereset app_name
copy the result into psql and run it.
"""

import os
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir))))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3%z&f40a$^688kmdjlf1&uwp2^-^%i998@5xuo&5j7!1g#wd@='

ALLOWED_HOSTS = ['*']

ASGI_APPLICATION = 'activities.routing.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6655)],
            'group_expiry': 7200,
            'expiry': 30,
            'capacity': 1500
        }
    }
}


# Application definition

INSTALLED_APPS = [
    'channels',
    'account.apps.AccountConfig',
    'activity.apps.ActivityConfig',
    'usergroups.apps.UsergroupsConfig',
    'scheduling.apps.SchedulingConfig',
    'wall.apps.WallConfig',
    'competitions.apps.CompetitionsConfig',
    'vacancies.apps.VacanciesConfig',
    'multiplayer.apps.MultiplayerConfig',
    'notify.apps.NotifyConfig',
    'chat.apps.ChatConfig',
    'character.apps.CharacterConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django_extensions',
    'parler',
    'easy_thumbnails',
    'cookielaw'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'activities.language_subdomain_middleware.LanguageSubdomainMiddleware',
#    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'global_login_required.GlobalLoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

ROOT_URLCONF = 'activities.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages'
            ],
        },
    },
]

WSGI_APPLICATION = 'activities.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

#global login required exceptions
PUBLIC_PATHS = [
    r'^/account/.*'
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

PARLER_LANGUAGES = {
    None: (
        {'code': 'en'},
        {'code': 'de'}
    ),
    'default': {
        'fallback': 'en',
        'hide_untranslated': False
    }
}

LANGUAGES = (
    ('de', _('Deutsch')),
    ('en', _('Englisch')),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale/'),
)

LANGUAGE_CODE = 'de'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')


LOGIN_REDIRECT_URL = 'account:home'
LOGIN_URL = 'account:login'
LOGOUT_URL = 'account:logout'
LOGOUT_REDIRECT_URL = '/account/login/'

# Email stuff

EMAIL_HOST = 'smtp.web.de'
EMAIL_HOST_USER = 'myactivities.net@web.de'
EMAIL_HOST_PASSWORD = 'My new password!'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'myactivities.net@web.de'

AUTH_USER_MODEL = 'account.User'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
