"""
ANSI based utility functions for the multi-con module
"""

import sys


def clear_line() -> None:
    """
    Clears a line using ansi escape characters
    """
    sys.stdout.write('\033[1A\033[K')


def clear_lines(num: int) -> None:
    """
    Calls clear_line n times
    """
    for _ in range(num):
        clear_line()


def clear_terminal() -> None:
    """
    Clears the terminal using ansi escape sequences
    """
    print("\033[2J")
    print("\033[3J")
