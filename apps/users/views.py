from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from apps.users.models import AppUser
from apps.schools.models import School
from apps.inspections.models import Inspection
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm

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

    # ===== ADMIN =====
    if role == AppUser.Role.ADMIN:
        total_schools = School.objects.count()
        total_users = AppUser.objects.count()
        total_inspections = Inspection.objects.count()
        recent_inspections = Inspection.objects.order_by("-date")[:5]

        context.update({
            "total_schools": total_schools,
            "total_users": total_users,
            "total_inspections": total_inspections,
            "recent_inspections": recent_inspections,
        })
        template = "users/admin_dashboard.html"

    # ===== MANAGER =====
    elif role == AppUser.Role.MANAGER:
        schools = user.schools.all()  # M2M or FK depending on your setup
        inspections = Inspection.objects.filter(school__in=schools).order_by("-date")[:5]

        context.update({
            "schools": schools,
            "recent_inspections": inspections,
        })
        template = "users/manager_dashboard.html"

    # ===== INSPECTOR =====
    elif role == AppUser.Role.INSPECTOR:
        assigned_schools = user.inspection_schools.all()
        inspections = Inspection.objects.filter(inspector=user).order_by("-date")[:5]

        context.update({
            "assigned_schools": assigned_schools,
            "upcoming_inspections": inspections,
        })
        template = "users/inspector_dashboard.html"

    # ===== KITCHEN STAFF =====
    else:
        school = getattr(user, "school", None)
        inspections = Inspection.objects.filter(school=school).order_by("-date")[:5] if school else []

        context.update({
            "school": school,
            "recent_inspections": inspections,
        })
        template = "users/kitchen_dashboard.html"

    return render(request, template, context)
