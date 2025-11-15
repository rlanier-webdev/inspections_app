from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .forms import InspectionForm
from apps.users.models import AppUser
from django.core.paginator import Paginator
from .models import Inspection, CorrectiveAction, InspectionItem
from apps.schools.models import School
from .forms import InspectionItemFormSet
from django.db import models


@login_required
def inspection_create(request):
    user = request.user

    if user.appuser.role not in [AppUser.Role.ADMIN, AppUser.Role.INSPECTOR]:
        raise PermissionDenied("You do not have permission to create inspections.")

    if request.method == "POST":
        form = InspectionForm(request.POST, user=user)
        if form.is_valid():
            inspection = form.save(commit=False)

            # 1. Automatically assign the school's manager
            school = form.cleaned_data["school"]
            managers = school.managers.all()

            if managers.exists():
                inspection.manager = managers.first()
            else:
                inspection.manager = None

            inspection.save()

            # 2. Create inspection items with None=True by default
            if inspection.checklist:
                for checklist_item in inspection.checklist.items.all():
                    InspectionItem.objects.create(
                        inspection=inspection,
                        checklist_item=checklist_item,
                        passed=None,  # <-- Now allowed
                    )

            return redirect("inspections:inspection_detail", pk=inspection.pk)

    else:
        form = InspectionForm(user=user)

    return render(request, "inspections/inspection_create.html", {"form": form})


@login_required
def inspection_list(request):
    user = request.user.appuser

    inspections = Inspection.objects.select_related(
        "school", "inspector", "manager", "checklist"
    )

    # Restrict kitchen user visibility
    if user.role == AppUser.Role.KITCHEN:
        inspections = inspections.filter(
            school__in=user.kitchen_schools.all()
        )

    # Manager only sees their schools
    elif user.role == AppUser.Role.MANAGER:
        inspections = inspections.filter(
            school__in=user.managed_schools.all()
        )

    # Inspector only sees their inspections
    elif user.role == AppUser.Role.INSPECTOR:
        inspections = inspections.filter(inspector=user)

    # Admin sees all → no filter

    # Filters
    school_id = request.GET.get("school")
    status = request.GET.get("status")
    date = request.GET.get("date")

    if school_id:
        inspections = inspections.filter(school_id=school_id)
    if status:
        inspections = inspections.filter(status=status)
    if date:
        inspections = inspections.filter(date=date)

    # Sorting
    sort_by = request.GET.get("sort", "-date")
    inspections = inspections.order_by(sort_by)

    # Current sort indicators
    if sort_by.startswith('-'):
        current_sort = sort_by[1:]
        sort_direction = 'desc'
    else:
        current_sort = sort_by
        sort_direction = 'asc'

    return render(request, 'inspections/inspection_list.html', {
        "inspections": inspections,
        "schools": School.objects.all(),
        "selected_school": school_id,
        "selected_status": status,
        "selected_date": date,
        "current_sort": current_sort,
        "sort_direction": sort_direction,
    })



@login_required
def inspection_detail(request, pk):
    inspection = get_object_or_404(
        Inspection.objects.select_related(
            "school", "inspector", "manager", "checklist"
        ),
        pk=pk
    )

    user = request.user.appuser

    # Admin: full access
    if user.role == AppUser.Role.ADMIN:
        pass

    # Manager: must manage this school
    elif user.role == AppUser.Role.MANAGER:
        if inspection.school not in user.managed_schools.all():
            raise PermissionDenied()

    # Inspector: must be assigned to this inspection
    elif user.role == AppUser.Role.INSPECTOR:
        if inspection.inspector != user:
            raise PermissionDenied()

    # Kitchen: must belong to this school
    elif user.role == AppUser.Role.KITCHEN:
        if inspection.school not in user.kitchen_schools.all():
            raise PermissionDenied()

    else:
        raise PermissionDenied()

    unresolved_actions = CorrectiveAction.objects.filter(
        inspection_item__inspection=inspection,
        status__in=["OPEN", "IN_PROGRESS", "AWAITING_REINSPECTION"]
    )

    return render(request, "inspections/inspection_detail.html", {
        "inspection": inspection,
        "unresolved_actions": unresolved_actions,
    })




@login_required
def inspection_perform(request, pk):
    inspection = get_object_or_404(
        Inspection.objects.select_related("school", "inspector", "manager", "checklist")
        .prefetch_related("inspection_items__checklist_item"),
        pk=pk
    )

    user = request.user.appuser

    # -------------------------------------------------
    # 1. PERMISSIONS
    # -------------------------------------------------
    if user.role not in (AppUser.Role.ADMIN, AppUser.Role.INSPECTOR):
        raise PermissionDenied("You do not have permission to perform this inspection.")

    if user.role == AppUser.Role.INSPECTOR and inspection.inspector != user:
        raise PermissionDenied("This inspection is not assigned to you.")

    # -------------------------------------------------
    # 2. Detect reinspection type
    # -------------------------------------------------
    action_id = request.GET.get("action")           # reinspect ONE item
    reinspect_all = request.GET.get("reinspect_all")  # reinspect all failed items

    # Which items should appear in the form?
    if action_id:
        inspection_items_qs = inspection.inspection_items.filter(
            corrective_actions__pk=action_id
        )
    elif reinspect_all:
        # Only items tied to unresolved corrective actions
        inspection_items_qs = inspection.inspection_items.filter(
            corrective_actions__status__in=[
                CorrectiveAction.Status.OPEN,
                CorrectiveAction.Status.IN_PROGRESS,
                CorrectiveAction.Status.AWAITING_REINSPECTION,
            ]
        )
    else:
        # Normal inspection mode
        inspection_items_qs = inspection.inspection_items.all()

    # -------------------------------------------------
    # 3. Determine if inspection should be read-only
    # -------------------------------------------------
    has_unresolved_actions = CorrectiveAction.objects.filter(
        inspection_item__inspection=inspection,
        status__in=[
            CorrectiveAction.Status.OPEN,
            CorrectiveAction.Status.IN_PROGRESS,
            CorrectiveAction.Status.AWAITING_REINSPECTION,
        ]
    ).exists()

    # Completed = PASSED or COMPLETED, but inspector can redo failed inspections
    is_completed = (
        inspection.status in [Inspection.Status.PASSED, Inspection.Status.COMPLETED]
        and not has_unresolved_actions
    )

    # NEVER lock in reinspection mode
    if action_id or reinspect_all:
        is_completed = False

    # Formset
    ItemFormSet = InspectionItemFormSet(queryset=inspection_items_qs)

    # -------------------------------------------------
    # 4. Process POST
    # -------------------------------------------------
    if request.method == "POST":
        formset = InspectionItemFormSet(request.POST, queryset=inspection_items_qs)

        if formset.is_valid():
            formset.save()

            # -----------------------------------------
            # REINSPECTION (single or bulk)
            # -----------------------------------------
            if action_id or reinspect_all:

                actions = CorrectiveAction.objects.filter(
                    inspection_item__in=inspection_items_qs
                )

                for action in actions:
                    # Update action based on pass/fail result
                    if action.inspection_item.passed:
                        action.status = CorrectiveAction.Status.REINSPECTED
                    else:
                        action.status = CorrectiveAction.Status.OPEN
                    action.save()

                # Reevaluate inspection status
                still_unresolved = CorrectiveAction.objects.filter(
                    inspection_item__inspection=inspection,
                    status__in=[
                        CorrectiveAction.Status.OPEN,
                        CorrectiveAction.Status.IN_PROGRESS,
                        CorrectiveAction.Status.AWAITING_REINSPECTION,
                    ]
                ).exists()

                inspection.status = (
                    Inspection.Status.FAILED if still_unresolved
                    else Inspection.Status.PASSED
                )
                inspection.save()

                return redirect("inspections:inspection_detail", pk=inspection.pk)

            # -----------------------------------------
            # NORMAL INSPECTION FLOW
            # -----------------------------------------
            if "complete_inspection" in request.POST:
                failed_items = inspection.inspection_items.filter(passed=False)

                if failed_items.exists():
                    inspection.status = Inspection.Status.FAILED

                    school = inspection.school

                    # Create corrective actions
                    for item in failed_items:
                        assigned_user = (
                            school.kitchen_staff.first()
                            or school.managers.first()
                            or None
                        )

                        CorrectiveAction.objects.create(
                            inspection_item=item,
                            assigned_to=assigned_user,
                            description=f"Correct issue: {item.checklist_item.text}",
                        )
                else:
                    inspection.status = Inspection.Status.PASSED
            else:
                inspection.status = Inspection.Status.PENDING

            inspection.save()
            return redirect("inspections:inspection_detail", pk=inspection.pk)

    else:
        formset = ItemFormSet

    # -------------------------------------------------
    # 5. Render Template
    # -------------------------------------------------
    return render(request, "inspections/inspection_perform.html", {
        "inspection": inspection,
        "formset": formset,
        "is_completed": is_completed,
        "action_id": action_id,
        "reinspect_all": reinspect_all,
    })



@login_required
def corrective_action_list(request):
    user = request.user.appuser

    # ADMIN – sees all actions
    if user.role == AppUser.Role.ADMIN:
        actions = CorrectiveAction.objects.all()

    # MANAGER – actions in their schools OR assigned to them
    elif user.role == AppUser.Role.MANAGER:
        manager_schools = user.managed_schools.all()
        actions = CorrectiveAction.objects.filter(
            models.Q(assigned_to=user) |
            models.Q(inspection_item__inspection__school__in=manager_schools)
        ).distinct()

    # INSPECTOR – actions from inspections they performed
    elif user.role == AppUser.Role.INSPECTOR:
        actions = CorrectiveAction.objects.filter(
            inspection_item__inspection__inspector=user
        )

    # KITCHEN – assigned to them OR tied to their schools
    elif user.role == AppUser.Role.KITCHEN:
        kitchen_schools = user.kitchen_schools.all()
        actions = CorrectiveAction.objects.filter(
            models.Q(assigned_to=user) |
            models.Q(inspection_item__inspection__school__in=kitchen_schools)
        ).distinct()

    else:
        actions = CorrectiveAction.objects.none()

    return render(request, "inspections/corrective_action_list.html", {
        "actions": actions,
    })


@login_required
def corrective_action_detail(request, pk):
    action = get_object_or_404(CorrectiveAction, pk=pk)

    # Always try to fetch AppUser profile
    try:
        user_profile = request.user.appuser
    except AppUser.DoesNotExist:
        user_profile = None

    # PERMISSIONS

    is_superuser = request.user.is_superuser
    is_admin = user_profile and user_profile.role == AppUser.Role.ADMIN
    is_manager = user_profile and user_profile.role == AppUser.Role.MANAGER
    is_assigned = user_profile and user_profile == action.assigned_to

    # Allowed users
    allowed = is_superuser or is_admin or is_manager or is_assigned

    if not allowed:
        raise PermissionDenied("You do not have permission to view this corrective action.")

    # PROCESS RESOLUTION
    if request.method == "POST":
        action.status = CorrectiveAction.Status.RESOLVED
        action.save()
        return redirect("inspections:corrective_action_list")

    return render(request, "inspections/corrective_action_detail.html", {
        "action": action,
    })



@login_required
def corrective_action_assign(request, pk):
    action = get_object_or_404(CorrectiveAction, pk=pk)

    # Permissions: Admin & Manager only
    user = request.user.appuser
    if request.user.is_superuser:
        pass
    elif user.role not in (AppUser.Role.ADMIN, AppUser.Role.MANAGER):
        raise PermissionDenied("Only admins and managers can reassign corrective actions.")

    if request.method == "POST":
        new_assigned_id = request.POST.get("assigned_to")

        if new_assigned_id:
            try:
                new_assigned_user = AppUser.objects.get(id=new_assigned_id)
                action.assigned_to = new_assigned_user
                action.save()
            except AppUser.DoesNotExist:
                pass  # ignore invalid input, shouldn't happen

        return redirect("inspections:corrective_action_list")


@login_required
def reinspect_action(request, pk):
    action = get_object_or_404(CorrectiveAction, pk=pk)
    user = request.user.appuser

    # permissions
    allowed = (
        request.user.is_superuser or
        user.role in [
            AppUser.Role.ADMIN,
            AppUser.Role.MANAGER,
            AppUser.Role.INSPECTOR
        ]
    )
    if not allowed:
        raise PermissionDenied()

    # Move corrective action to "awaiting reinspection"
    action.status = CorrectiveAction.Status.AWAITING_REINSPECTION
    action.save()

    # Redirect to the inspection perform screen
    # Pass a QUERY parameter so the view knows to show only this item
    inspection = action.inspection_item.inspection
    return redirect(
        "inspections:inspection_perform",
        pk=inspection.pk
    )
