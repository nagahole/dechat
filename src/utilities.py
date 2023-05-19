import time


def is_integer(s: str) -> bool:
    if s[0] == "-":
        s = s[1:]
    return s.isnumeric()


def format_time_period(seconds: float):
    s = seconds // 1
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    s = int(s)
    m = int(m)
    h = int(h)
    d = int(d)

    is_seconds = False

    if d != 0:
        res = f"{d} days, {h} hours, {m} minutes and {s} seconds"
    elif h != 0:
        res = f"{h} hours, {m} minutes and {s} seconds"
    elif m != 0:
        res = f"{m} minutes and {s} seconds"
    else:
        res = f"{s} seconds"
        is_seconds = True

    if not is_seconds:
        res += f" ({int(round(seconds))} seconds)"

    return res


def unix_to_str(unix_time: int) -> str:
    return f"[{time.strftime('%H:%M:%S', time.localtime(unix_time))}]"


def smart_split(s: str) -> list[str]:
    return list(filter(lambda s: s != "", s.split()))