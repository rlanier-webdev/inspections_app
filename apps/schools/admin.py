from django.contrib import admin
from .models import School

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'phone_number')
    search_fields = ('name', 'city', 'state')
    list_filter = ('state',)
    filter_horizontal = ('managers', 'kitchen_staff', 'inspectors')
