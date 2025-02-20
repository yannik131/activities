from django.urls import path
from . import views

app_name = 'competitions'

urlpatterns = [
    path('test/', views.test, name='test'),
    path('user_overview/', views.user_overview, name='user_overview'),
    path('overview/<int:activity_id>/', views.overview, name='overview'),
    path('create_match/<int:activity_id>/', views.create_match, name='create_match'),
    path('match_detail/<int:match_id>/', views.match_detail, name='match_detail'),
    path('delete_match/<int:match_id>/', views.delete_match, name='delete_match'),
    path('edit_match/<int:match_id>/', views.edit_match, name='edit_match'),
    path('create_tournament/<int:activity_id>/', views.create_tournament, name='create_tournament'),
    path('tournament_detail/<tournament_id>/', views.tournament_detail, name='tournament_detail'),
    path('edit_tournament/<int:tournament_id>/', views.edit_tournament, name='edit_tournament'),
    path('add_tournament_member/<int:tournament_id>/<int:user_id>/', views.add_tournament_member, name='add_tournament_member'),
    path('remove_member/<str:model>/<int:instance_id>/<int:user_id>/<str:who>/', views.remove_member, name='remove_member'),
    path('tournament_standings/<int:tournament_id>/', views.tournament_standings, name='tournament_standings'),
    path('delete_tournament/<int:tournament_id>/', views.delete_tournament, name='delete_tournament'),
    path('game_plan/<int:tournament_id>/<int:round_number>/', views.game_plan, name='game_plan'),
    path('generate_next_round/<int:tournament_id>/', views.generate_next_round, name='generate_next_round'),
    path('change_score/<int:round_id>/<int:matchup_index>/', views.change_score, name='change_score'),
    path('close_round/<int:round_id>/', views.close_round, name='close_round')

]