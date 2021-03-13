from django.urls import path
from . import views

app_name = 'activity'

urlpatterns = [
    path('join/<str:activity_name>/', views.join, name='join'),
    path('leave/<str:activity_name>/', views.leave, name='leave'),
    path('detail/<str:activity_name>/', views.detail, name='detail'),
    path('list/', views.activity_list, name='list'),
    path('list/<str:search_string>/', views.activity_list, name='list'),
    path('category_detail/<str:category_name>/', views.category_detail, name='category_detail'),
    path('category_list/', views.category_list, name='category_list'),
    path('no_source/', views.no_source, name='no_source')
]