from django import template
from django.utils.timezone import utc
from datetime import datetime, timedelta

register = template.Library()


def _now():
    return datetime.utcnow().replace(tzinfo=utc)


def abs_timedelta(delta):
    """Returns an "absolute" value for a timedelta, always representing a
    time distance."""
    if delta.days < 0:
        now = _now()
        return now - (now + delta)
    return delta


def date_and_delta(value):
    """Turn a value into a date and a timedelta which represents how long ago
    it was.  If that's not possible, return (None, value)."""
    now = _now()
    if isinstance(value, datetime):
        date = value
        delta = now - value
    elif isinstance(value, timedelta):
        date = now - value
        delta = value
    else:
        try:
            value = int(value)
            delta = timedelta(seconds=value)
            date = now - delta
        except (ValueError, TypeError):
            return None, value
    return date, abs_timedelta(delta)


def shortnaturaldelta(value):
    """Given a timedelta or a number of seconds, return a natural
    representation of the amount of time elapsed."""
    date, delta = date_and_delta(value)
    if date is None:
        return value

    seconds = abs(delta.seconds)
    days = abs(delta.days)
    years = days // 365
    days = days % 365

    if not years and days < 1:
        if seconds <= 1:
            return "1s"
        elif seconds < 60:
            return "%ds" % (seconds)
        elif 60 <= seconds < 3600:
            return "%dm %ds" % (seconds // 60, seconds % 60)
        elif 3600 <= seconds:
            return "%dh %dm %ds" % (seconds // 3600, seconds % 3600 // 60, seconds % 60)
    elif years == 0:
        return "%dd %dh %dm" % (days, seconds % 86400 // 3600, seconds % 3600 // 60)
    else:
        return "%dy %dd %dh" % (years, days, seconds % 86400 // 3600)


@register.filter
def shortnaturaltime(value):
    """Given a datetime or a number of seconds, return a natural representation
    of that time in a resolution that makes sense.  This is more or less
    compatible with Django's ``naturaltime`` filter."""
    # now = _now()
    date, delta = date_and_delta(value)
    if date is None:
        return value
    # determine tense by value only if datetime/timedelta were passed
    # if isinstance(value, (datetime, timedelta)):
    #     future = date > now

    delta = shortnaturaldelta(delta)

    if delta == "a moment":
        return "now"

    return delta
