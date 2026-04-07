from django.conf import settings
from django.core.cache import cache
from baselines.logic.baseline_logic import get_daily_baseline

BASELINE_CACHE_KEY = "daily_baseline"
BASELINE_CACHE_TIMEOUT = 60 * 60  # 1 hora


def get_baseline_data():
    if settings.USE_CACHE:
        return get_baseline_from_cache()

    baseline = get_daily_baseline()
    return {
        "data": baseline,
        "cache_source": "source"
    }


def get_baseline_from_cache():
    cached_baseline = cache.get(BASELINE_CACHE_KEY)

    if cached_baseline is not None:
        return {
            "data": cached_baseline,
            "cache_source": "cache"
        }

    baseline = get_daily_baseline()
    cache.set(BASELINE_CACHE_KEY, baseline, timeout=BASELINE_CACHE_TIMEOUT)
    return {
        "data": baseline,
        "cache_source": "source"
    }