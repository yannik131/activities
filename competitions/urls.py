from django.urls import path
from . import views

app_name = 'competitions'

urlpatterns = [
    path('user_overview/', views.user_overview, name='user_overview'),
    path('overview/<int:activity_id>/', views.overview, name='overview'),
    path('create_match/<int:activity_id>/', views.create_match, name='create_match'),
    path('match_detail/<int:match_id>/', views.match_detail, name='match_detail'),
    path('delete_match/<int:match_id>/', views.delete_match, name='delete_match')
]