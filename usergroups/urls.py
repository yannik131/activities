from django.urls import path
from . import views

app_name = 'usergroups'


urlpatterns = [
    path('group_list/<int:id>/', views.group_list, name='group_list'),
    path('group_list/', views.group_list, name='group_list'),
    path('group_detail/<int:id>/', views.group_detail, name='group_detail'),
    path('edit_group/<int:id>/', views.edit_group, name='edit_group'),
    path('create_group/<int:id>/', views.create_group, name='create_group'),
    path('delete_group/<int:id>/', views.delete_group, name='delete_group'),
    path('leave_group/<int:id>/', views.leave_group, name='leave_group'),
    path('kick_out/<int:group_id>/<int:user_id>/', views.kick_out, name='kick_out')
]