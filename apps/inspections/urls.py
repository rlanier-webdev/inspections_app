from django.urls import path
from . import views

app_name = 'inspections'

urlpatterns = [
    path('', views.inspection_list, name='inspection_list'),
    path('<int:pk>/', views.inspection_detail, name='inspection_detail'),
    path("create/", views.inspection_create, name="inspection_create"),
    path("<int:pk>/perform/", views.inspection_perform, name="inspection_perform"),
    path("actions/", views.corrective_action_list, name="corrective_action_list"),
    path("actions/<int:pk>/", views.corrective_action_detail, name="corrective_action_detail"),
    path("actions/<int:pk>/assign/", views.corrective_action_assign, name="corrective_action_assign"),
    path("<int:inspection_id>/actions/", views.corrective_action_list, name="corrective_action_list_by_inspection"),
    path("actions/<int:pk>/reinspect/", views.reinspect_action, name="reinspect_action"),

]
