import jwt
import datetime
from django.conf import settings
from django.http import JsonResponse
from .models import AuditLog, SecurityAlert

def generate_token(request):
    tenant_id = request.GET.get('tenant_id', 'cliente-a')
    payload = {
        'user_id': f'user-{tenant_id}',
        'tenant_id': tenant_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
    return JsonResponse({'token': token, 'tenant_id': tenant_id})

def audit_logs(request):
    logs = list(AuditLog.objects.values().order_by('-timestamp')[:50])
    return JsonResponse({'logs': logs})

def security_alerts(request):
    alerts = list(SecurityAlert.objects.values().order_by('-timestamp')[:50])
    return JsonResponse({'alerts': alerts})
