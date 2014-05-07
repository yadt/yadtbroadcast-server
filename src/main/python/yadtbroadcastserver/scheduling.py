from datetime import time, datetime, timedelta


def seconds_to_midnight(offset_seconds=60):
    now = datetime.now()
    next_midnight = datetime.combine(now, time()) + timedelta(days=1, seconds=offset_seconds)
    return int((next_midnight - now).total_seconds())
