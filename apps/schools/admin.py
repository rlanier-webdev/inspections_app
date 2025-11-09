# apps/schools/admin.py
from django.contrib import admin
from .models import School

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'is_active', 'created_at')
    search_fields = ('name', 'address')
    list_filter = ('is_active',)
    filter_horizontal = ('users',)