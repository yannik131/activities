from django.urls import path
from . import views

app_name = 'notify'

urlpatterns = [
    path('delete/<int:notification_id>/', views.delete, name='delete')
]