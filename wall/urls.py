from django.urls import path
from . import views

app_name = 'wall'


urlpatterns = [
    path('create_post/<str:app_label>/<str:model>/<int:id>/', views.create_post, name='create_post'),
    path('delete_post/<int:id>/<path:path>/', views.delete_post, name='delete_post'),
    path('create_comment/<int:id>/<path:path>/', views.create_comment, name='create_comment'),
    path('delete_comment/<int:id>/<path:path>/', views.delete_comment, name='delete_comment')
]