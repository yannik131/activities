from django.urls import path
from . import views

app_name = 'activity'

urlpatterns = [
    path('join/<str:name>/', views.join, name='join'),
    path('leave/<str:name>/', views.leave, name='leave'),
    path('detail/<str:name>/', views.detail, name='detail'),
    path('list/', views.activity_list, name='list'),
    path('category_detail/<int:id>/', views.category_detail, name='category_detail'),
    path('category_list/', views.category_list, name='category_list')
]