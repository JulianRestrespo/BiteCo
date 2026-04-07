from django.urls import path
from .views import check_anomalies

urlpatterns = [
    path('alerts/check/', check_anomalies, name='check_anomalies'),
]