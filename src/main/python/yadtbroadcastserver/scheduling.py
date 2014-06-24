from __future__ import division

from datetime import time, datetime, timedelta
from math import ceil


def _now():
    return datetime.now()


def seconds_to_midnight(offset_seconds=0):
    now = _now()
    next_midnight = datetime.combine(now, time()) + timedelta(days=1, seconds=offset_seconds)
    datetime_to_midnight = next_midnight - now
    return ceil(datetime_to_midnight.seconds + datetime_to_midnight.days * 24 * 3600) + 1
