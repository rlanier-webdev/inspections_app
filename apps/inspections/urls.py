from django.urls import path
from . import views

app_name = 'inspections'

urlpatterns = [
    path('', views.inspection_list, name='inspection_list'),
    path('<int:pk>/', views.inspection_detail, name='inspection_detail'),
]
