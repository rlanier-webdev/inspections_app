from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .forms import InspectionForm
from apps.users.models import AppUser
from django.core.paginator import Paginator
from .models import Inspection, CorrectiveAction
from apps.schools.models import School
from .forms import InspectionItemFormSet


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
                inspection.manager = managers.first()  # or choose logic below
            else:
                inspection.manager = None  # no manager assigned to school

            # 2. Inspector is already selected in the form
            inspection.save()

            # 3. Create inspection items for the selected checklist
            if inspection.checklist:
                for item in inspection.checklist.items.all():
                    inspection.inspection_items.create(checklist_item=item)

            return redirect("inspections:inspection_detail", pk=inspection.pk)

    else:
        form = InspectionForm(user=user)

    return render(request, "inspections/inspection_create.html", {"form": form})



@login_required
def inspection_list(request):
    inspections = Inspection.objects.select_related('school', 'inspector', 'manager', 'checklist')

    # Filters
    school_id = request.GET.get('school')
    status = request.GET.get('status')
    date = request.GET.get('date')

    if school_id:
        inspections = inspections.filter(school_id=school_id)
    if status:
        inspections = inspections.filter(status=status)
    if date:
        inspections = inspections.filter(date=date)

    # Sorting
    sort_by = request.GET.get('sort', '-date')  # Default: newest first
    valid_sort_fields = ['date', 'status', 'school__name', '-date', '-status', '-school__name']
    if sort_by not in valid_sort_fields:
        sort_by = '-date'
    inspections = inspections.order_by(sort_by)

    # Determine current column and direction
    if sort_by.startswith('-'):
        current_sort = sort_by[1:]
        sort_direction = 'desc'
    else:
        current_sort = sort_by
        sort_direction = 'asc'

    # Pagination
    paginator = Paginator(inspections, 20)  # 20 per page
    
    # If filters or sorting change, reset pagination to first page
    query_params = request.GET.copy()
    if any(k in query_params for k in ['school', 'status', 'date', 'sort']):
        # User changed filters or sort — reset to first page
        page_number = None
    else:
        page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    # Compute sort prefix for pagination links
    sort_prefix = '-' if sort_direction == 'desc' else ''

    context = {
        'page_obj': page_obj,
        'inspections': page_obj.object_list,  # For your table
        'schools': School.objects.all(),
        'selected_school': school_id,
        'selected_status': status,
        'selected_date': date,
        'current_sort': current_sort,
        'sort_direction': sort_direction,
        'sort_prefix': sort_prefix,
    }

    return render(request, 'inspections/inspection_list.html', context)


@login_required
def inspection_detail(request, pk):
    inspection = get_object_or_404(
        Inspection.objects.select_related('school', 'inspector', 'manager', 'checklist')
        .prefetch_related('inspection_items__checklist_item'),
        pk=pk
    )
    context = {
        'inspection': inspection
    }
    return render(request, 'inspections/inspection_detail.html', context)


@login_required
def inspection_perform(request, pk):
    inspection = get_object_or_404(
        Inspection.objects.select_related("school", "inspector", "manager", "checklist")
        .prefetch_related("inspection_items__checklist_item"),
        pk=pk
    )

    # Permission: only assigned inspector or admin can perform
    if request.user.appuser.role not in (AppUser.Role.ADMIN, AppUser.Role.INSPECTOR):
        raise PermissionDenied("You do not have permission to perform this inspection.")

    # If inspector, must be the assigned one
    if request.user.appuser.role == AppUser.Role.INSPECTOR:
        if inspection.inspector != request.user.appuser:
            raise PermissionDenied("This inspection is not assigned to you.")

    # If inspection already completed, display read-only
    is_completed = inspection.status in (
        inspection.Status.PASSED,
        inspection.Status.FAILED,
        inspection.Status.COMPLETED
    )

    ItemFormSet = InspectionItemFormSet(
        queryset=inspection.inspection_items.all(),
    )

    if request.method == "POST":
        formset = InspectionItemFormSet(request.POST, queryset=inspection.inspection_items.all())

        if formset.is_valid():

            # Save all items first
            formset.save()

            # Determine status
            if "complete_inspection" in request.POST:
                failed_items = inspection.inspection_items.filter(passed=False)

                if failed_items.exists():
                    inspection.status = Inspection.Status.FAILED

                    # AUTO-CREATE CORRECTIVE ACTIONS
                    for item in failed_items:
                        # Decide who gets assigned
                        # Prefer Kitchen Staff → else Manager → else None
                        school = inspection.school

                        assigned_user = (
                            school.kitchen_staff.first()
                            or school.managers.first()
                            or None
                        )

                        CorrectiveAction.objects.create(
                            inspection_item=item,
                            assigned_to=assigned_user,
                            description=f"Correct issue: {item.checklist_item.text}"
                        )

                else:
                    inspection.status = Inspection.Status.PASSED

            else:
                inspection.status = Inspection.Status.PENDING  # Save as draft

            inspection.save()

            return redirect("inspections:inspection_detail", pk=inspection.pk)

    else:
        formset = ItemFormSet

    return render(request, "inspections/inspection_perform.html", {
        "inspection": inspection,
        "formset": formset,
        "is_completed": is_completed,
    })


@login_required
def corrective_action_list(request):
    user = request.user.appuser

    if user.role == AppUser.Role.ADMIN:
        actions = CorrectiveAction.objects.all()

    elif user.role == AppUser.Role.MANAGER:
        actions = CorrectiveAction.objects.filter(
            assigned_to__in=request.user.appuser.managed_schools.values_list("kitchen_staff", flat=True)
        ) | CorrectiveAction.objects.filter(assigned_to=user)

    elif user.role == AppUser.Role.KITCHEN:
        actions = CorrectiveAction.objects.filter(assigned_to=user)

    elif user.role == AppUser.Role.INSPECTOR:
        # Inspectors only see actions for their inspections
        actions = CorrectiveAction.objects.filter(
            inspection_item__inspection__inspector=user
        )

    else:
        actions = CorrectiveAction.objects.none()

    return render(request, "inspections/corrective_action_list.html", {
        "actions": actions,
    })


@login_required
def corrective_action_detail(request, pk):
    action = get_object_or_404(CorrectiveAction, pk=pk)

    # --- PERMISSIONS ---
    if request.user.is_superuser:
        allowed = True
    else:
        try:
            user_profile = request.user.appuser
        except AppUser.DoesNotExist:
            raise PermissionDenied("You do not have an AppUser profile.")

        allowed = (
            user_profile.role == AppUser.Role.ADMIN or
            user_profile.role == AppUser.Role.MANAGER or
            user_profile == action.assigned_to
        )

    if not allowed:
        raise PermissionDenied("You do not have permission to view this action.")

    # --- HANDLE POST ---
    if request.method == "POST":
        action.status = CorrectiveAction.Status.RESOLVED
        action.save()
        return redirect("inspections:corrective_action_list")

    # --- RENDER ---
    return render(request, "inspections/corrective_action_detail.html", {
        "action": action,
    })
