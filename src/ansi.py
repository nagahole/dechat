import sys


def clear_line() -> None:
    sys.stdout.write('\033[1A\033[K')


def clear_lines(n: int) -> None:
    for _ in range(n):
        clear_line()