from django.urls import path
from . import views

app_name = 'multiplayer'

urlpatterns = [
    path('lobby/<str:activity_name>/', views.lobby, name='lobby'),
    path('create_match/<str:activity_name>/', views.create_match, name='create_match'),
    path('game/<int:match_id>/', views.game, name='game'),
    path('get_online_list/<int:activity_id>/', views.get_online_list, name='get_online_list'),
    path('match/<int:match_id>/', views.match, name='match'),
    path('enter_match/<int:match_id>/', views.enter_match, name='enter_match'),
    path('leave_match/<int:match_id>/', views.leave_match, name='leave_match')
]