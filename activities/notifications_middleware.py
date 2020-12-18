try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object

from notify.models import Notification


class NotificationsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_anonymous:
            request.notifications = Notification.objects.filter(recipient=request.user)