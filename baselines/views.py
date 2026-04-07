from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from baselines.logic.baseline_logic import get_daily_baseline


def daily_baseline(request):
    baseline = get_daily_baseline()
    return JsonResponse(baseline)