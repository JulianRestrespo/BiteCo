from django.shortcuts import render

# Create your views here
import time
from django.http import JsonResponse
from reports.services.report_service import get_report_data
from core.utils.instance import get_instance_name


def monthly_report(request):
    start_time = time.perf_counter()

    report_result = get_report_data()
    report = report_result["data"]

    end_time = time.perf_counter()
    processing_time_ms = round((end_time - start_time) * 1000, 3)

    report["processing_time_ms"] = processing_time_ms
    report["instance"] = get_instance_name()
    report["cache_source"] = report_result["cache_source"]

    return JsonResponse(report)