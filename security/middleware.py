import time
import jwt
from django.conf import settings
from django.http import JsonResponse
from .models import AuditLog, SecurityAlert

PROTECTED_PREFIXES = [
    '/reports/monthly/',
]

class TenantAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if not any(path.startswith(p) for p in PROTECTED_PREFIXES):
            return self.get_response(request)

        start = time.time()

        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JsonResponse({'error': 'token requerido'}, status=401)

        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'token expirado'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'token invalido'}, status=401)

        user_tenant = payload.get('tenant_id')
        user_id = payload.get('user_id', 'desconocido')
        resource_tenant = request.GET.get('tenant_id')

        if resource_tenant and user_tenant != resource_tenant:
            elapsed = (time.time() - start) * 1000
            ip = request.META.get('REMOTE_ADDR')

            AuditLog.objects.create(
                user_id=user_id,
                user_tenant=user_tenant,
                resource_tenant=resource_tenant,
                path=path,
                ip=ip,
                response_time_ms=elapsed,
            )
            SecurityAlert.objects.create(
                user_id=user_id,
                user_tenant=user_tenant,
                resource_tenant=resource_tenant,
                path=path,
            )

            return JsonResponse({
                'error': 'acceso no autorizado',
                'security_response_time_ms': round(elapsed, 2)
            }, status=403)

        request.user_tenant = user_tenant
        request.user_id = user_id
        return self.get_response(request)