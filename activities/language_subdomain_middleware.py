try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object

from django.utils import translation


class LanguageSubdomainMiddleware(MiddlewareMixin):

    def process_request(self, request):
        domain = request.META['HTTP_HOST']
        language = domain.split('.')[0]
        if language == 'www':
            language = 'en'
        request.session['django_language'] = language
        translation.activate(language)
