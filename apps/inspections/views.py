from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
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
