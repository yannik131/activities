from django.urls import path
from . import views

app_name = 'competitions'

urlpatterns = [
    path('overview/<int:activity_id>/', views.overview, name='overview')
]