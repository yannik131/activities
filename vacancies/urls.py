from django.urls import path
from . import views

app_name = 'vacancies'

urlpatterns = [
    path('create_vacancies/<str:app_label>/<str:model>/<int:id>/', views.create_vacancies, name='create_vacancies'),
    path('create_invitation/<str:app_label>/<str:model>/<int:id>/', views.create_invitation, name='create_invitation'),
    path('delete_vacancy/<int:id>/', views.delete_vacancy, name='delete_vacancy'),
    path('delete_invitation/<int:id>/', views.delete_invitation, name='delete_invitation'),
    path('edit_vacancy/<int:id>/', views.edit_vacancy, name='edit_vacancy'),
    path('accept_invitation/<int:id>/', views.accept_invitation, name='accept_invitation'),
    path('apply_for_vacancy/<int:id>/', views.apply_for_vacancy, name='apply_for_vacancy'),
    path('review_vacancy/<int:id>/', views.review_vacancy, name='review_vacancy'),
    path('accept_application/<int:id>/', views.accept_application, name='accept_application'),
    path('decline_application/<int:id>/', views.decline_application, name='decline_application'),
    path('delete_application/<int:id>/', views.delete_application, name='delete_application'),
    path('application_list/', views.application_list, name='application_list')
]

