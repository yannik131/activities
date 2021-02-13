from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from usergroups.models import UserGroup
from .models import Appointment
from django.http import HttpResponseRedirect, HttpResponseForbidden
from .forms import AppointmentForm
from account.views import handler403


@login_required
def create_appointment(request, id):
    group = UserGroup.objects.get(id=id)
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.group = group
            appointment.save()
            return HttpResponseRedirect(group.get_absolute_url())
    else:
        form = AppointmentForm()
    return render(request, 'scheduling/create_appointment.html', dict(form=form, group=group))


@login_required
def delete_appointment(request, id):
    appointment = Appointment.objects.get(id=id)
    if request.user == appointment.group.admin:
        appointment.delete()
        return HttpResponseRedirect(appointment.group.get_absolute_url())
    return handler403(request)


@login_required
def confirm_appointment(request, id):
    appointment = Appointment.objects.get(id=id)
    appointment.participants.add(request.user)
    return HttpResponseRedirect(appointment.group.get_absolute_url())


@login_required
def decline_appointment(request, id):
    appointment = Appointment.objects.get(id=id)
    appointment.cancellations.add(request.user)
    return HttpResponseRedirect(appointment.group.get_absolute_url())


@login_required
def cancel_confirmation(request, id):
    appointment = Appointment.objects.get(id=id)
    appointment.participants.remove(request.user)
    return HttpResponseRedirect(appointment.group.get_absolute_url())


@login_required
def cancel_cancellation(request, id):
    appointment = Appointment.objects.get(id=id)
    appointment.cancellations.remove(request.user)
    return HttpResponseRedirect(appointment.group.get_absolute_url())