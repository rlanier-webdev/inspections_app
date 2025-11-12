from django.db import models
from apps.users.models import AppUser

class School(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Relationships
    managers = models.ManyToManyField(
        AppUser,
        related_name="managed_schools",
        blank=True,
        limit_choices_to={'role': AppUser.Role.MANAGER}
    )
    kitchen_staff = models.ManyToManyField(
        AppUser,
        related_name="kitchen_schools",
        blank=True,
        limit_choices_to={'role': AppUser.Role.KITCHEN}
    )
    inspectors = models.ManyToManyField(
        AppUser,
        related_name="inspection_schools",
        blank=True,
        limit_choices_to={'role': AppUser.Role.INSPECTOR}
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"
        ordering = ['name']