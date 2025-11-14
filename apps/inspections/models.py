from django.db import models
from apps.users.models import AppUser
from apps.schools.models import School
from apps.checklists.models import Checklist, ChecklistItem


class Inspection(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        PASSED = "PASSED", "Passed"

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="inspections")
    inspector = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspections_as_inspector",
        limit_choices_to={'role': AppUser.Role.INSPECTOR}
    )
    manager = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspections_as_manager",
        limit_choices_to={'role': AppUser.Role.MANAGER}
    )
    checklist = models.ForeignKey(
        Checklist,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspections"
    )
    date = models.DateField()
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Inspection"
        verbose_name_plural = "Inspections"

    def __str__(self):
        return f"{self.school.name} - {self.date} ({self.get_status_display()})"
    
    def initialize_items(self):
        for checklist_item in self.checklist.items.all():
            InspectionItem.objects.get_or_create(
                inspection=self,
                checklist_item=checklist_item,
                defaults=None  # or None if you want blank
            )



class InspectionItem(models.Model):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="inspection_items")
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE)
    passed = models.BooleanField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.inspection} - {self.checklist_item.text}"
    

class CorrectiveAction(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        AWAITING_REINSPECTION = "AWAITING_REINSPECTION", "Awaiting Reinspection"
        REINSPECTED = "REINSPECTED", "Reinspected"

    inspection_item = models.ForeignKey(
        InspectionItem,
        on_delete=models.CASCADE,
        related_name="corrective_actions"
    )
    assigned_to = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corrective_actions"
    )
    description = models.TextField()
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Action for {self.inspection_item.checklist_item.text}"
    
    class Meta:
        verbose_name = "Corrective Action"
        verbose_name_plural = "Corrective Actions"