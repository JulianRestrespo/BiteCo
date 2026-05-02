import json
import time
from pathlib import Path

from django.conf import settings

from reports.services.report_service import get_report_data


CIRCUIT_STATE_FILE = settings.BASE_DIR / "availability_state.json"
ASR_REACTION_THRESHOLD_MS = 500


def _default_state():
    return {
        "failure_mode": False,
        "circuit_state": "closed"
    }


def save_circuit_state(state):
    with open(CIRCUIT_STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file)


def get_circuit_state():
    if not Path(CIRCUIT_STATE_FILE).exists():
        save_circuit_state(_default_state())

    with open(CIRCUIT_STATE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def set_failure_mode(mode: bool):
    state = {
        "failure_mode": mode,
        "circuit_state": "open" if mode else "closed"
    }

    save_circuit_state(state)
    return state


def generate_primary_report():
    report_result = get_report_data()
    report = report_result["data"].copy()

    report["handler_used"] = "primary"
    report["backup_handler_activated"] = False
    report["cache_source"] = report_result["cache_source"]

    return report


def generate_rescue_report():
    return {
        "project_id": "project-001",
        "month": "2026-04",
        "currency": "USD",
        "total_cost": 1200,
        "report_type": "rescue_monthly_report",
        "handler_used": "rescue",
        "backup_handler_activated": True,
        "services": [
            {
                "name": "EC2",
                "cost": 500,
                "usage": 120
            },
            {
                "name": "S3",
                "cost": 300,
                "usage": 200
            },
            {
                "name": "RDS",
                "cost": 400,
                "usage": 80
            }
        ]
    }


def generate_managed_report(force_failure=False):
    reaction_start = time.perf_counter()

    state = get_circuit_state()
    failure_mode = state["failure_mode"] or force_failure

    if not failure_mode:
        report = generate_primary_report()

        return {
            **report,
            "availability_experiment": "normal_operation",
            "failure_mode": False,
            "circuit_state": "closed",
            "reaction_time_ms": 0,
            "asr_threshold_ms": ASR_REACTION_THRESHOLD_MS,
            "asr_met": True
        }

    report = generate_rescue_report()

    reaction_end = time.perf_counter()
    reaction_time_ms = round((reaction_end - reaction_start) * 1000, 3)

    return {
        **report,
        "availability_experiment": "failure_with_rescue_handler",
        "failure_mode": True,
        "circuit_state": "open",
        "reaction_time_ms": reaction_time_ms,
        "asr_threshold_ms": ASR_REACTION_THRESHOLD_MS,
        "asr_met": reaction_time_ms < ASR_REACTION_THRESHOLD_MS
    }