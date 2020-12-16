try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object

from django.utils import translation, timezone


class LanguageSubdomainMiddleware(MiddlewareMixin):
    def process_request(self, request):
        domain = request.META['HTTP_HOST']
        language = domain.split('.')[0]
        if language not in ['en', 'de']:
            language = 'de'
        request.session['django_language'] = language
        request.LANGUAGE_CODE = language
        translation.activate(language)
