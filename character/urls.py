from django.urls import path, reverse_lazy
from . import views

app_name = 'character'

urlpatterns = [
    path('overview/', views.overview, name='overview'),
    path('quiz/', views.quiz, name='quiz'),
    path('reset_quiz/', views.reset_quiz, name='reset_quiz')
]