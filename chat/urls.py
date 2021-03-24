from django.urls import path
from . import views

app_name = 'chat'


urlpatterns = [
    path('room/<str:app_label>/<str:model>/<int:id>/', views.chat_room, name='chat_room')
]