from .models import Notification
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404


@login_required
def delete(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    if request.user.id is not notification.recipient.id:
        return HttpResponseForbidden()
    notification.delete()
    return HttpResponse(status=204)