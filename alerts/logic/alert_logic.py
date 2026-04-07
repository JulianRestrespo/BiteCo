from baselines.services.baseline_service import get_baseline_data
from reports.services.report_service import get_report_data


def detect_anomalies():
    baseline_result = get_baseline_data()
    report_result = get_report_data()

    baseline = baseline_result["data"]
    report = report_result["data"]

    anomalies = []

    baseline_services = {
        service["name"]: service for service in baseline["services"]
    }

    for service in report["services"]:
        service_name = service["name"]

        if service_name not in baseline_services:
            continue

        baseline_service = baseline_services[service_name]

        cost_limit = baseline_service["cost_average"] * 1.2
        usage_limit = baseline_service["usage_average"] * 1.2

        cost_anomaly = service["cost"] > cost_limit
        usage_anomaly = service["usage"] > usage_limit

        if cost_anomaly:
            anomalies.append({
                "type": "service_cost",
                "service": service_name,
                "message": "Service cost exceeds baseline by more than 20%",
                "current_value": service["cost"],
                "baseline_value": baseline_service["cost_average"],
            })

        if usage_anomaly:
            anomalies.append({
                "type": "service_usage",
                "service": service_name,
                "message": "Service usage exceeds baseline by more than 20%",
                "current_value": service["usage"],
                "baseline_value": baseline_service["usage_average"],
            })

    return {
        "project_id": report["project_id"],
        "anomaly_found": len(anomalies) > 0,
        "anomalies": anomalies,
        "alert_count": len(anomalies),
        "baseline_cache_source": baseline_result["cache_source"],
        "report_cache_source": report_result["cache_source"],
    }