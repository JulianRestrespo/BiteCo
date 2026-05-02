from django.shortcuts import render

# Create your views here
import time

from django.http import JsonResponse

from availability.services import generate_managed_report
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


def managed_report(request):
    start_time = time.perf_counter()

    force_failure = request.GET.get("force_failure", "false").lower() == "true"

    result = generate_managed_report(force_failure=force_failure)

    end_time = time.perf_counter()
    total_processing_time_ms = round((end_time - start_time) * 1000, 3)

    result["total_processing_time_ms"] = total_processing_time_ms
    result["instance"] = get_instance_name()

    return JsonResponse(result)