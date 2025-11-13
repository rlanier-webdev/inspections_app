from django import forms
from .models import Inspection
from apps.users.models import AppUser
from apps.schools.models import School
from django.forms import modelformset_factory
from .models import InspectionItem, Inspection

class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = ["school", "inspector", "checklist", "date", "status", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Bootstrap styling
        for field_name in ["school", "inspector", "checklist"]:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({"class": "form-select"})

        # Managers only see their schools
        if user and user.appuser.role == AppUser.Role.MANAGER:
            self.fields['school'].queryset = user.appuser.managed_schools.all()
        else:
            self.fields['school'].queryset = School.objects.all()

        # Inspectors list
        self.fields["inspector"].queryset = AppUser.objects.filter(
            role=AppUser.Role.INSPECTOR
        )


class InspectionItemForm(forms.ModelForm):
    class Meta:
        model = InspectionItem
        fields = ["passed", "notes"]
        widgets = {
            "passed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

InspectionItemFormSet = modelformset_factory(
    InspectionItem,
    form=InspectionItemForm,
    extra=0
)