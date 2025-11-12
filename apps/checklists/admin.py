from django.contrib import admin
from .models import Checklist, ChecklistItem


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 1
    fields = ("text", "order")
    ordering = ("order",)


@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "item_count")
    search_fields = ("name",)
    inlines = [ChecklistItemInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Number of Items"


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("text", "checklist", "order")
    list_filter = ("checklist",)
    ordering = ("checklist", "order")
    search_fields = ("text", "checklist__name") 
