def get_monthly_report():
    return {
        "project_id": "project-001",
        "month": "2026-04",
        "currency": "USD",
        "total_cost": 1200,
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