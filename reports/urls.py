from django.urls import path
from .views import monthly_report
from .views import managed_report

urlpatterns = [
    path('reports/monthly/', monthly_report, name='monthly_report'),
    path('reports/managed/', managed_report, name='managed_report'),
]