from django.shortcuts import render

# Create your views here.
import time
from django.http import JsonResponse
from alerts.logic.alert_logic import detect_anomalies
from core.utils.instance import get_instance_name


def check_anomalies(request):
    start_time = time.perf_counter()

    result = detect_anomalies()

    end_time = time.perf_counter()
    processing_time_ms = round((end_time - start_time) * 1000, 3)

    result["processing_time_ms"] = processing_time_ms
    result["instance"] = get_instance_name()

    return JsonResponse(result)