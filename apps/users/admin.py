from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import AppUser
from .forms import AppUserForm


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    form = AppUserForm
    list_display = ('full_name', 'email_address', 'role', 'is_staff', 'date_joined')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    list_filter = ('role', 'is_staff', 'date_joined')

    readonly_fields = ('view_user_link',)
    fields = (
        'view_user_link',
        'first_name', 'last_name', 'email',
        'role', 'phone_number', 'is_staff'
    )

    def full_name(self, obj):
        return obj.user.get_full_name() if obj.user else "Not linked"
    full_name.admin_order_field = 'user__first_name'
    full_name.short_description = 'Full Name'

    def email_address(self, obj):
        return obj.user.email if obj.user else "Not linked"
    email_address.admin_order_field = 'user__email'
    email_address.short_description = 'Email'

    def view_user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "No linked user"
    view_user_link.short_description = "Linked User"

    # 🚫 Disable manual creation in admin
    def has_add_permission(self, request):
        return False
