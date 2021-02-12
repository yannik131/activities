"""activities URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import account.views

urlpatterns = [
    path('', account.views.home),
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),
    path('activity/', include('activity.urls')),
    path('usergroups/', include('usergroups.urls')),
    path('scheduling/', include('scheduling.urls')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('wall/', include('wall.urls')),
    path('competitions/', include('competitions.urls')),
    path('vacancies/', include('vacancies.urls')),
    path('notifications/', include('notify.urls')),
    path('multiplayer/', include('multiplayer.urls'))
]

handler404 = "account.views.handler404"
handler403 = "account.views.handler403"
handler500 = "account.views.handler500"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)