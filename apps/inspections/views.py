from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Inspection
from apps.schools.models import School

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
    sort_by = request.GET.get('sort', '-date')  # default newest first
    inspections = inspections.order_by(sort_by)

    # Determine current column and toggle direction
    if sort_by.startswith('-'):
        current_sort = sort_by[1:]
        sort_direction = 'desc'
    else:
        current_sort = sort_by
        sort_direction = 'asc'

    context = {
        'inspections': inspections,
        'schools': School.objects.all(),
        'selected_school': school_id,
        'selected_status': status,
        'selected_date': date,
        'current_sort': current_sort,
        'sort_direction': sort_direction,  # 'asc' or 'desc'
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
