from django.urls import path
from .views import daily_baseline

urlpatterns = [
    path('baselines/daily/', daily_baseline, name='daily_baseline'),
]