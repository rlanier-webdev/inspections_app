from django.urls import path
from . import views

app_name = "schools"   # optional but recommended

urlpatterns = [
    path('<int:pk>/', views.school_detail, name='school_detail'),
]
