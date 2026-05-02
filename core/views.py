from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from core.utils.instance import get_instance_name


from django.http import JsonResponse
from core.utils.instance import get_instance_name


def home(request):
    return JsonResponse({
        "message": "BiteCo API is running",
        "instance": get_instance_name(),
        "available_endpoints": [
            "/health/",
            "/reports/monthly/",
            "/reports/managed/",
            "/reports/managed/?force_failure=true",
            "/baselines/daily/",
            "/alerts/check/",
            "/availability/status/",
            "/availability/simulate-failure/?mode=on",
            "/availability/simulate-failure/?mode=off"
        ]
    })


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "service": "bite-co",
        "instance": get_instance_name()
    })