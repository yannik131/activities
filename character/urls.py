from django.urls import path, reverse_lazy
from . import views

app_name = 'character'

urlpatterns = [
    path('overview/', views.overview, name='overview')
]