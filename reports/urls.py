from django.urls import path
from .views import monthly_report

urlpatterns = [
    path('reports/monthly/', monthly_report, name='monthly_report'),
]