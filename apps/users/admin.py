from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import AppUser
from .forms import AppUserForm


# ============================================================
#   COLOR BADGE FOR ROLE (Professional Look)
# ============================================================

def role_badge(obj):
    COLORS = {
        "ADMIN": "#007bff",     # Blue
        "MANAGER": "#6610f2",   # Purple
        "KITCHEN": "#fd7e14",   # Orange
        "INSPECTOR": "#198754", # Green
    }

    color = COLORS.get(obj.role, "#6c757d")

    return format_html(
        '<span style="background:{}; color:white; padding:3px 8px; '
        'font-size:12px; border-radius:4px;">{}</span>',
        color,
        obj.get_role_display()
    )

role_badge.short_description = "Role"


# ============================================================
#   ADMIN: APP USER
# ============================================================

@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    form = AppUserForm

    # How rows appear in the list view
    list_display = (
        "full_name",
        "email_address",
        role_badge,
        "is_staff",
        "date_joined",
    )

    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone_number",
    )

    list_filter = (
        "role",
        "is_staff",
        "date_joined",
    )

    ordering = ("user__first_name", "user__last_name")

    # Prevent accidental creation of orphaned AppUsers
    def has_add_permission(self, request):
        return False

    # Make Django User link read-only and visible
    readonly_fields = ("view_user_link", "date_joined")

    # Clean layout with professional fieldsets
    fieldsets = (
        ("Linked Django User", {
            "fields": ("view_user_link",),
            "description": "This AppUser is automatically linked to a Django auth user."
        }),
        ("Personal Details", {
            "fields": (
                "first_name",
                "last_name",
                "email",
                "phone_number",
            )
        }),
        ("Role & Access", {
            "fields": (
                "role",
                "is_staff",
            )
        }),
        ("System Info", {
            "fields": ("date_joined",),
            "classes": ("collapse",),
        })
    )

    # -----------------------------
    #   FIELD HELPERS
    # -----------------------------

    def full_name(self, obj):
        return obj.user.get_full_name() if obj.user else "Not linked"
    full_name.admin_order_field = "user__first_name"
    full_name.short_description = "Full Name"

    def email_address(self, obj):
        return obj.user.email if obj.user else "Not linked"
    email_address.admin_order_field = "user__email"
    email_address.short_description = "Email"

    def view_user_link(self, obj):
        if not obj.user:
            return "No linked user"

        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html(
            '<a href="{}" style="font-weight:bold;">{}</a>',
            url,
            obj.user.username
        )
    view_user_link.short_description = "Linked Django User"
