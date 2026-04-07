def get_daily_baseline():
    return {
        "project_id": "project-001",
        "baseline_date": "2026-04-07",
        "currency": "USD",
        "total_cost_average": 1000,
        "services": [
            {
                "name": "EC2",
                "cost_average": 400,
                "usage_average": 100
            },
            {
                "name": "S3",
                "cost_average": 250,
                "usage_average": 180
            },
            {
                "name": "RDS",
                "cost_average": 350,
                "usage_average": 70
            }
        ]
    }