from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from core.utils.instance import get_instance_name


def home(request):
    return JsonResponse({
        "message": "BiteCo API is running",
        "instance": get_instance_name(),
        "available_endpoints": [
            "/health/",
            "/reports/monthly/",
            "/baselines/daily/",
            "/alerts/check/"
        ]
    })


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "service": "bite-co",
        "instance": get_instance_name()
    })