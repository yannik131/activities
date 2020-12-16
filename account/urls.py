from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'account'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(success_url=reverse_lazy('account:password_reset_done')), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('account:password_reset_complete')), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
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
    path('view_friendship/<int:id>/', views.view_friendship, name='view_friendship'),
    path('about/', views.about, name='about')
]