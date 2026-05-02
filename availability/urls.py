from django.urls import path

from .views import availability_status, simulate_failure


urlpatterns = [
    path("availability/status/", availability_status, name="availability_status"),
    path("availability/simulate-failure/", simulate_failure, name="simulate_failure"),
]