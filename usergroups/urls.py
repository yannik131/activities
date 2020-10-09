from django.urls import path
from . import views

app_name = 'usergroups'


urlpatterns = [
    path('group_list/<int:id>/', views.group_list, name='group_list'),
    path('group_list/', views.group_list, name='group_list'),
    path('group_detail/<int:id>/', views.group_detail, name='group_detail'),
    path('edit_group/<int:id>/', views.edit_group, name='edit_group'),
    path('create_group/<int:id>/', views.create_group, name='create_group'),
    path('create_vacancies/<int:id>/', views.create_vacancies, name='create_vacancies'),
    path('create_invitation<int:id>/', views.create_invitation, name='create_invitation'),
    path('delete_vacancy/<int:id>/', views.delete_vacancy, name='delete_vacancy'),
    path('delete_invitation/<int:id>/', views.delete_invitation, name='delete_invitation'),
    path('edit_vacancy/<int:id>/', views.edit_vacancy, name='edit_vacancy'),
    path('accept_invitation/<int:id>/', views.accept_invitation, name='accept_invitation'),
    path('delete_group/<int:id>/', views.delete_group, name='delete_group'),
    path('leave_group/<int:id>/', views.leave_group, name='leave_group'),
    path('kick_out/<int:group_id>/<int:user_id>/', views.kick_out, name='kick_out'),
    path('apply_for_vacancy/<int:id>/', views.apply_for_vacancy, name='apply_for_vacancy'),
    path('review_vacancy/<int:id>/', views.review_vacancy, name='review_vacancy'),
    path('accept_application/<int:id>/', views.accept_application, name='accept_application'),
    path('decline_application/<int:id>/', views.decline_application, name='decline_application'),
    path('delete_application/<int:id>/', views.delete_application, name='delete_application')
]