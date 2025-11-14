from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import School
from apps.inspections.models import Inspection, CorrectiveAction


@login_required
def school_detail(request, pk):
    school = get_object_or_404(School, pk=pk)

    # Recent inspections for this school
    inspections = Inspection.objects.filter(school=school).order_by("-date")[:10]

    # Corrective actions tied to this school
    corrective_actions = CorrectiveAction.objects.filter(
        inspection_item__inspection__school=school
    ).select_related(
        "inspection_item__inspection",
        "assigned_to"
    )

    context = {
        "school": school,
        "inspections": inspections,
        "corrective_actions": corrective_actions,
    }
    return render(request, "schools/school_detail.html", context)
