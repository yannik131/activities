from django.urls import path
from . import views

app_name = 'competitions'

urlpatterns = [
    path('overview/<int:activity_id>/', views.overview, name='overview'),
    path('create_match/<int:activity_id>/', views.create_match, name='create_match'),
    path('match_detail/<int:match_id>', views.match_detail, name='match_detail')
]