from django.conf import settings
from django.core.cache import cache
from reports.logic.report_logic import get_monthly_report

REPORT_CACHE_KEY = "monthly_report"
REPORT_CACHE_TIMEOUT = 60 * 60  # 1 hora


def get_report_data():
    if settings.USE_CACHE:
        return get_report_from_cache()

    report = get_monthly_report()
    return {
        "data": report,
        "cache_source": "source"
    }


def get_report_from_cache():
    cached_report = cache.get(REPORT_CACHE_KEY)

    if cached_report is not None:
        return {
            "data": cached_report,
            "cache_source": "cache"
        }

    report = get_monthly_report()
    cache.set(REPORT_CACHE_KEY, report, timeout=REPORT_CACHE_TIMEOUT)
    return {
        "data": report,
        "cache_source": "source"
    }