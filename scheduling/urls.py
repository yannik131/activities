from django.urls import path
from . import views

app_name = 'scheduling'

urlpatterns = [
    path('create_appointment/<int:id>/', views.create_appointment, name='create_appointment'),
    path('delete_appointment/<int:id>/', views.delete_appointment, name='delete_appointment'),
    path('confirm_appointment/<int:id>/', views.confirm_appointment, name='confirm_appointment'),
    path('decline_appointment/<int:id>/', views.decline_appointment, name='decline_appointment'),
    path('cancel_confirmation/<int:id>/', views.cancel_confirmation, name='cancel_confirmation'),
    path('cancel_cancellation/<int:id>/', views.cancel_cancellation, name='cancel_cancellation')
]
