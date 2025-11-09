from django.db import models
from django.contrib.auth.models import User

class AppUser(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        KITCHEN = "KITCHEN", "Kitchen Staff"
        INSPECTOR = "INSPECTOR", "Inspector"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.KITCHEN)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def save(self, *args, **kwargs):
        # Sync is_staff with superuser
        if self.user.is_superuser:
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role})"

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email_address(self):
        return self.user.email
