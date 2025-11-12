from django.contrib import admin
from .models import Inspection, InspectionItem


class InspectionItemInline(admin.TabularInline):
    model = InspectionItem
    extra = 1
    fields = ("checklist_item", "passed", "notes")
    autocomplete_fields = ("checklist_item",)


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ("school", "inspector", "manager", "date", "status")
    list_filter = ("status", "date", "school", "inspector")
    search_fields = ("school__name", "inspector__user__first_name", "manager__user__first_name")
    date_hierarchy = "date"
    inlines = [InspectionItemInline]
    autocomplete_fields = ("school", "inspector", "manager", "checklist")

    fieldsets = (
        (None, {
            "fields": ("school", "inspector", "manager", "checklist", "date", "status")
        }),
        ("Additional Info", {
            "fields": ("notes",),
            "classes": ("collapse",),
        }),
    )


@admin.register(InspectionItem)
class InspectionItemAdmin(admin.ModelAdmin):
    list_display = ("inspection", "checklist_item", "passed")
    list_filter = ("passed", "inspection__status")
    search_fields = ("inspection__school__name", "checklist_item__text")
