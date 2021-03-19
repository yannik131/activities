from django.urls import path, reverse_lazy
from . import views

app_name = 'character'

urlpatterns = [
    path('overview/<str:category_name>/', views.overview, name='overview'),
    path('overview/', views.overview, name='overview'),
    path('quiz/', views.quiz, name='quiz'),
    path('quiz/<int:limit>/', views.quiz, name='quiz'),
    path('reset_quiz/', views.reset_quiz, name='reset_quiz'),
    path('edit_weights/<int:activity_id>/', views.edit_weights, name='edit_weights')
]