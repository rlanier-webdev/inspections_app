# apps/schools/models.py
from django.db import models
from apps.users.models import AppUser

class School(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    users = models.ManyToManyField(
        AppUser,
        related_name='schools',
        blank=True,
        help_text="Assign users (admins, inspectors, kitchen staff) to this school."
    )

    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"

    def __str__(self):
        return self.name
