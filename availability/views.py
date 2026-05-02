from django.shortcuts import render

from django.http import JsonResponse

from availability.services import (
    get_circuit_state,
    set_failure_mode,
)


def availability_status(request):
    state = get_circuit_state()

    return JsonResponse({
        "component": "availability",
        "failure_mode": state["failure_mode"],
        "circuit_state": state["circuit_state"]
    })


def simulate_failure(request):
    mode = request.GET.get("mode", "off").lower()

    if mode == "on":
        state = set_failure_mode(True)
        message = "Primary report handler failure activated"
    elif mode == "off":
        state = set_failure_mode(False)
        message = "Primary report handler failure deactivated"
    else:
        return JsonResponse({
            "error": "Invalid mode. Use mode=on or mode=off"
        }, status=400)

    return JsonResponse({
        "message": message,
        "failure_mode": state["failure_mode"],
        "circuit_state": state["circuit_state"]
    })
