"""
Useful utility functions that may be used across multiple files
"""

# False-positive import error
# pylint: disable=import-error

import time
from src.constants import MAX_PORT_VALUE


def is_integer(string: str) -> bool:
    """
    Returns whether an input string is an integer or not
    """
    if string[0] == "-":
        string = string[1:]
    return string.isnumeric()


def format_time_period(seconds: float):
    """
    Formats a time period into a more understandable combination of units
    of time
    """
    secs = seconds // 1
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    days, hours = divmod(hours, 24)

    secs = int(secs)
    mins = int(mins)
    hours = int(hours)
    days = int(days)

    is_seconds = False

    if days != 0:
        res = f"{days} days, {hours} hours, {mins} minutes and {secs} seconds"
    elif hours != 0:
        res = f"{hours} hours, {mins} minutes and {secs} seconds"
    elif mins != 0:
        res = f"{mins} minutes and {secs} seconds"
    else:
        res = f"{secs} seconds"
        is_seconds = True

    if not is_seconds:
        res += f" ({int(round(seconds))} seconds)"

    return res


def unix_to_str(unix_time: int) -> str:
    """
    Converts unix time to '[HH:MM:SS]' format
    """
    return f"[{time.strftime('%H:%M:%S', time.localtime(unix_time))}]"


def smart_split(string: str) -> list[str]:
    """
    Splits a string by whitespace and filters out empty splits
    """
    return list(filter(lambda s: s != "", string.split()))


def split_hostname_port(string: str) -> tuple[str | None, int | None]:
    """
    Returns the hostname and port from a string as a tuple.

    Returns None, None if input is invalid
    """
    splits = string.split(":")

    hostname = ":".join(splits[0:-1])

    if not is_integer(splits[-1]):
        return None, None

    port = int(splits[-1])

    if not 0 <= port <= MAX_PORT_VALUE:
        return None, None

    return hostname, port


def flush_print(*args, **kwargs):
    """
    Flushes by default
    """
    if "flush" in kwargs:
        print(*args, **kwargs)
    else:
        print(*args, **kwargs, flush=True)
