from django.contrib import admin
from .models import Location, User
from wall.models import Post

class PostAdmin(admin.ModelAdmin):
    list_display = ['created', 'approved', 'media_mime_type']

admin.site.register(User)
admin.site.register(Location)
admin.site.register(Post, PostAdmin)