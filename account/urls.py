from django.urls import path, include
from . import views

app_name = 'account'

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='edit'),
    path('edit_address/', views.edit_address, name='edit_address'),
    path('detail/<int:id>/', views.detail, name='detail'),
    path('send_friend_request/<int:target_id>/', views.send_friend_request, name='send_friend_request'),
    path('send_custom_friend_request/', views.send_custom_friend_request, name='send_custom_friend_request'),
    path('destroy_friendship/<int:id>/', views.destroy_friendship, name='destroy_friendship'),
    path('friend_requests_list/', views.friend_requests_list, name='friend_requests_list'),
    path('accept_request/<int:id>/', views.accept_request, name='accept_request'),
    path('decline_request/<int:id>/', views.decline_request, name='decline_request'),
    path('delete_request/<int:id>/', views.delete_request, name='delete_request'),
    path('user_post_list/', views.user_post_list, name='user_post_list'),
    path('view_friendship/<int:id>/', views.view_friendship, name='view_friendship')
]