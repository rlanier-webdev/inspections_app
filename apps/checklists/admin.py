from django.contrib import admin
from django.utils.html import format_html
from .models import Checklist, ChecklistItem


# ============================================================
#   INLINE: CHECKLIST ITEMS
# ============================================================

class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 1
    fields = ("order", "text")
    ordering = ("order",)
    min_num = 1


# ============================================================
#   ADMIN: CHECKLIST
# ============================================================

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):

    list_display = ("name", "description_short", "created_at")
    search_fields = ("name", "description")
    list_filter = ("created_at",)
    ordering = ("name",)

    inlines = [ChecklistItemInline]

    readonly_fields = ("created_at",)

    fieldsets = (
        ("Checklist Info", {
            "fields": ("name", "description")
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )

    # Nicely formatted description preview
    def description_short(self, obj):
        if not obj.description:
            return "—"
        if len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description

    description_short.short_description = "Description"


# ============================================================
#   ADMIN: CHECKLIST ITEM (optional standalone)
# ============================================================

@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):

    list_display = ("checklist", "order", "text")
    list_filter = ("checklist",)
    search_fields = ("text", "checklist__name")
    ordering = ("checklist__name", "order")
    autocomplete_fields = ("checklist",)

    fieldsets = (
        ("Checklist Item", {
            "fields": ("checklist", "text", "order")
        }),
    )
