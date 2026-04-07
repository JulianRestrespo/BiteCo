from reports.logic.report_logic import get_monthly_report
from baselines.services.baseline_service import get_baseline_data


THRESHOLD_MULTIPLIER = 1.2


def find_service_baseline(service_name, baseline_services):
    for service in baseline_services:
        if service["name"] == service_name:
            return service
    return None


def detect_anomalies():
    report = get_monthly_report()
    baseline_result = get_baseline_data()
    baseline = baseline_result["data"]

    anomalies = []

    if report["total_cost"] > baseline["total_cost_average"] * THRESHOLD_MULTIPLIER:
        anomalies.append({
            "type": "total_cost",
            "message": "Total cost exceeds baseline by more than 20%",
            "current_value": report["total_cost"],
            "baseline_value": baseline["total_cost_average"]
        })

    for service in report["services"]:
        baseline_service = find_service_baseline(service["name"], baseline["services"])

        if baseline_service is None:
            continue

        if service["cost"] > baseline_service["cost_average"] * THRESHOLD_MULTIPLIER:
            anomalies.append({
                "type": "service_cost",
                "service": service["name"],
                "message": "Service cost exceeds baseline by more than 20%",
                "current_value": service["cost"],
                "baseline_value": baseline_service["cost_average"]
            })

        if service["usage"] > baseline_service["usage_average"] * THRESHOLD_MULTIPLIER:
            anomalies.append({
                "type": "service_usage",
                "service": service["name"],
                "message": "Service usage exceeds baseline by more than 20%",
                "current_value": service["usage"],
                "baseline_value": baseline_service["usage_average"]
            })

    return {
        "project_id": report["project_id"],
        "anomaly_found": len(anomalies) > 0,
        "anomalies": anomalies,
        "alert_count": len(anomalies),
        "baseline_cache_source": baseline_result["cache_source"]
    }