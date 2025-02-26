from django.shortcuts import render, get_object_or_404
from usergroups.models import UserGroup
from .models import Appointment
from django.http import HttpResponseRedirect
from .forms import AppointmentForm
from account.views import handler403


def create_appointment(request, id):
    group = get_object_or_404(UserGroup, id=id)
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.group = group
            appointment.creator = request.user
            appointment.save()
            return HttpResponseRedirect(group.get_absolute_url())
    else:
        form = AppointmentForm()
    return render(request, 'scheduling/create_appointment.html', dict(form=form, group=group))


def delete_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    if request.user in [appointment.group.admin, appointment.creator]:
        appointment.delete()
        return HttpResponseRedirect(appointment.group.get_absolute_url())
    return handler403(request)


def confirm_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    appointment.participants.add(request.user)
    return HttpResponseRedirect(appointment.group.get_absolute_url())


def decline_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    appointment.cancellations.add(request.user)
    return HttpResponseRedirect(appointment.group.get_absolute_url())


def cancel_confirmation(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    appointment.participants.remove(request.user)
    return HttpResponseRedirect(appointment.group.get_absolute_url())


def cancel_cancellation(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    appointment.cancellations.remove(request.user)
    return HttpResponseRedirect(appointment.group.get_absolute_url())