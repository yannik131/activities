from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'account'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(success_url=reverse_lazy('account:password_change_done')), name='password_change'),
    path('password_change/done/', views.password_change_done, name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(success_url=reverse_lazy('account:password_reset_done'), html_email_template_name='registration/password_reset_email.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('account:password_reset_complete')), name='password_reset_confirm'),
    path('password_reset_complete', views.password_reset_complete, name='password_reset_complete'),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='edit'),
    path('edit_address/', views.edit_address, name='edit_address'),
    path('detail/<str:username>/', views.detail, name='detail'),
    path('send_friend_request/<int:target_id>/', views.send_friend_request, name='send_friend_request'),
    path('send_custom_friend_request/', views.send_custom_friend_request, name='send_custom_friend_request'),
    path('destroy_friendship/<int:id>/', views.destroy_friendship, name='destroy_friendship'),
    path('friend_requests_list/', views.friend_requests_list, name='friend_requests_list'),
    path('accept_request/<int:id>/', views.accept_request, name='accept_request'),
    path('decline_request/<int:id>/', views.decline_request, name='decline_request'),
    path('delete_request/<int:id>/', views.delete_request, name='delete_request'),
    path('user_post_list/', views.user_post_list, name='user_post_list'),
    path('view_friendship/<int:id>/', views.view_friendship, name='view_friendship'),
    path('about/', views.about, name='about'),
    path('delete/', views.delete, name='delete'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('impressum/', views.impressum, name='impressum'),
    path('people_list/', views.people_list, name='people_list'),
    path('delete_marker/<int:marker_id>/', views.delete_marker, name='delete_marker')
]