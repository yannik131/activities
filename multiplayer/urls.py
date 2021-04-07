from django.urls import path
from . import views

app_name = 'multiplayer'

urlpatterns = [
    path('lobby/<str:activity_name>/', views.lobby, name='lobby'),
    path('lobby/<str:activity_name>/<str:extra>/', views.lobby, name='lobby'),
    path('create_match/<str:activity_name>/', views.create_match, name='create_match'),
    path('game/<str:activity_name>/<int:match_id>/', views.game, name='game'),
    path('match/<str:activity_name>/<int:match_id>/', views.match, name='match'),
    path('start_match/<str:activity_name>/<int:match_id>/', views.start_match, name='start_match'),
    path('enter_match/<str:activity_name>/<int:match_id>/', views.enter_match, name='enter_match'),
    path('leave_match/<str:activity_name>/<int:match_id>/', views.leave_match, name='leave_match')
]