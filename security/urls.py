from django.urls import path
from . import views

urlpatterns = [
    path('token/', views.generate_token),
    path('audit/', views.audit_logs),
    path('alerts/', views.security_alerts),
]
