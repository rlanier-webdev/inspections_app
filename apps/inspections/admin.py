from django.contrib import admin
from django.utils.html import format_html
from .models import Inspection, InspectionItem, CorrectiveAction


# ============================================================
#   STATUS BADGE UTILITY
# ============================================================

def colored_status(obj):
    COLOR_MAP = {
        "OPEN": "red",
        "IN_PROGRESS": "orange",
        "RESOLVED": "green",
        "FAILED": "red",
        "PASSED": "green",
        "PENDING": "gray",
        "COMPLETED": "blue",
    }

    color = COLOR_MAP.get(obj.status, "gray")

    return format_html(
        '<span style="background-color:{}; color:white; padding:4px 8px; '
        'border-radius:4px; font-size:12px;">{}</span>',
        color,
        obj.get_status_display()
    )

colored_status.short_description = "Status"


# ============================================================
#   INLINE: INSPECTION ITEMS
# ============================================================

class InspectionItemInline(admin.TabularInline):
    model = InspectionItem
    extra = 0
    fields = ("checklist_item", "passed", "notes")
    autocomplete_fields = ("checklist_item",)


# ============================================================
#   ADMIN: CORRECTIVE ACTION
# ============================================================

@admin.register(CorrectiveAction)
class CorrectiveActionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "inspection_item",
        "assigned_to",
        colored_status,
        "created_at",
    )

    list_filter = (
        "status",
        "assigned_to",
        "inspection_item__inspection__school",
        "inspection_item__inspection__inspector",
    )

    search_fields = (
        "description",
        "inspection_item__checklist_item__text",
        "assigned_to__user__first_name",
        "assigned_to__user__last_name",
        "inspection_item__inspection__school__name",
    )

    autocomplete_fields = ("assigned_to", "inspection_item")

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Corrective Action Details", {
            "fields": (
                "inspection_item",
                "assigned_to",
                "status",
                "description",
            )
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


# ============================================================
#   ADMIN: INSPECTION
# ============================================================

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):

    list_display = (
        "school",
        "inspector",
        "manager",
        "date",
        "status",
    )

    list_filter = (
        "status",
        "date",
        "school",
        "inspector",
        "manager",
    )

    search_fields = (
        "school__name",
        "inspector__user__first_name",
        "inspector__user__last_name",
        "manager__user__first_name",
        "manager__user__last_name",
    )

    date_hierarchy = "date"

    autocomplete_fields = ("school", "inspector", "manager", "checklist")

    readonly_fields = ("created_at", "updated_at")

    inlines = [
        InspectionItemInline,
    ]

    fieldsets = (
        ("Inspection Info", {
            "fields": (
                "school",
                "inspector",
                "manager",
                "checklist",
                "date",
                "status",
            )
        }),
        ("Notes", {
            "fields": ("notes",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    ordering = ("-date",)


# ============================================================
#   ADMIN: INSPECTION ITEM
# ============================================================

@admin.register(InspectionItem)
class InspectionItemAdmin(admin.ModelAdmin):

    list_display = (
        "inspection",
        "checklist_item",
        "passed",
        "notes"
    )

    list_filter = (
        "passed",
        "inspection__school",
        "inspection__status"
    )

    search_fields = (
        "inspection__school__name",
        "checklist_item__text",
        "notes"
    )

    autocomplete_fields = ("inspection", "checklist_item")
