from django.http import JsonResponse
from baselines.services.baseline_service import get_baseline_data


def daily_baseline(request):
    baseline_result = get_baseline_data()
    baseline = baseline_result["data"]
    baseline["cache_source"] = baseline_result["cache_source"]
    return JsonResponse(baseline)