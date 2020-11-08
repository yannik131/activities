from django.contrib import admin
from .models import Activity, Category
from parler.admin import TranslatableAdmin


@admin.register(Activity)
class ActivityAdmin(TranslatableAdmin):
    list_display = ['name', 'description']


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ['name', 'description']

