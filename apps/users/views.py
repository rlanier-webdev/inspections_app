from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from apps.users.models import AppUser
from apps.schools.models import School
from apps.inspections.models import Inspection
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from apps.inspections.models import CorrectiveAction

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    return redirect('login')

class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    form_class = AuthenticationForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


@login_required
def dashboard(request):
    user = request.user.appuser
    role = user.role

    context = {"user": user}

    # ========== ADMIN DASHBOARD ==========
    if role == AppUser.Role.ADMIN:
        total_schools = School.objects.count()
        total_users = AppUser.objects.count()
        total_inspections = Inspection.objects.count()

        recent_inspections = Inspection.objects.order_by("-date")[:5]
        total_actions = CorrectiveAction.objects.count()
        open_actions = CorrectiveAction.objects.filter(status=CorrectiveAction.Status.OPEN).count()
        in_progress_actions = CorrectiveAction.objects.filter(status=CorrectiveAction.Status.IN_PROGRESS).count()
        resolved_actions = CorrectiveAction.objects.filter(status=CorrectiveAction.Status.RESOLVED).count()

        recent_actions = CorrectiveAction.objects.select_related(
            "inspection_item__inspection__school",
            "assigned_to"
        ).order_by("-created_at")[:5]

        context.update({
            "total_schools": total_schools,
            "total_users": total_users,
            "total_inspections": total_inspections,
            "recent_inspections": recent_inspections,
            "total_actions": total_actions,
            "open_actions": open_actions,
            "in_progress_actions": in_progress_actions,
            "resolved_actions": resolved_actions,
            "recent_actions": recent_actions,
        })

        template = "users/admin_dashboard.html"

    # ========== MANAGER DASHBOARD ==========
    elif role == AppUser.Role.MANAGER:
        # CORRECT school relationship
        manager_schools = user.managed_schools.all()

        recent_inspections = Inspection.objects.filter(
            school__in=manager_schools
        ).order_by("-date")[:5]

        actions_requiring_oversight = CorrectiveAction.objects.filter(
            inspection_item__inspection__school__in=manager_schools,
            status__in=[
                CorrectiveAction.Status.OPEN,
                CorrectiveAction.Status.IN_PROGRESS
            ]
        ).select_related(
            "inspection_item__inspection__school",
            "assigned_to"
        )

        context.update({
            "schools": manager_schools,
            "recent_inspections": recent_inspections,
            "actions_requiring_oversight": actions_requiring_oversight,
            "action_count": actions_requiring_oversight.count(),
        })

        template = "users/manager_dashboard.html"

    # ========== INSPECTOR DASHBOARD ==========
    elif role == AppUser.Role.INSPECTOR:

        # Correct school relationship
        assigned_schools = user.inspection_schools.all()

        # Inspections this inspector has performed
        recent_inspections = Inspection.objects.filter(
            inspector=user
        ).order_by("-date")[:5]

        # Corrective actions created by inspections this inspector performed
        actions_created = CorrectiveAction.objects.filter(
            inspection_item__inspection__inspector=user
        ).select_related(
            "inspection_item__inspection__school",
            "assigned_to"
        ).order_by("-created_at")

        context.update({
            "assigned_schools": assigned_schools,
            "recent_inspections": recent_inspections,
            "actions_created": actions_created,
            "action_count": actions_created.count(),
        })

        template = "users/inspector_dashboard.html"


    # ========== KITCHEN STAFF DASHBOARD ==========
    else:
        kitchen_schools = user.kitchen_schools.all()

        recent_inspections = Inspection.objects.filter(
            school__in=kitchen_schools
        ).order_by("-date")[:5]

        assigned_actions = CorrectiveAction.objects.filter(
            assigned_to=user,
            status__in=[
                CorrectiveAction.Status.OPEN,
                CorrectiveAction.Status.IN_PROGRESS
            ]
        ).select_related(
            "inspection_item__inspection__school",
        )

        context.update({
            "kitchen_schools": kitchen_schools,
            "recent_inspections": recent_inspections,
            "assigned_actions": assigned_actions,
            "assigned_action_count": assigned_actions.count()
        })

        template = "users/kitchen_dashboard.html"

    return render(request, template, context)
