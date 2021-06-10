try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object

from django.utils import translation

def get_prefix(request):
    domain = request.META.get('HTTP_HOST')
    if domain:
        language = domain.split('.')[0]
        if language not in ['en', 'de']:
            language = 'de'
    else:
        language = 'de'
    return language


class LanguageSubdomainMiddleware(MiddlewareMixin):
    def process_request(self, request):
        language = get_prefix(request)
        request.session['django_language'] = language
        request.LANGUAGE_CODE = language
        translation.activate(language)
