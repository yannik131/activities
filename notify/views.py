from .models import Notification
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from account.views import handler403


@login_required
def delete(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    if request.user.id is not notification.recipient.id:
        return handler403(request)
    notification.delete()
    return HttpResponse(status=204)