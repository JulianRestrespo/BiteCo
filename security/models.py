from django.db import models

class AuditLog(models.Model):
    user_id = models.CharField(max_length=100)
    user_tenant = models.CharField(max_length=100)
    resource_tenant = models.CharField(max_length=100)
    path = models.CharField(max_length=200)
    ip = models.GenericIPAddressField()
    response_time_ms = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class SecurityAlert(models.Model):
    user_id = models.CharField(max_length=100)
    user_tenant = models.CharField(max_length=100)
    resource_tenant = models.CharField(max_length=100)
    path = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    