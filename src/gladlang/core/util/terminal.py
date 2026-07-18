"""Terminal utilities – set window title across platforms."""

import os
import sys

try:
    import ctypes
except ImportError:
    ctypes = None


def set_terminal_title(title):
    if not sys.stdout.isatty():
        return

    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except Exception:
            pass
        return

    try:
        sys.stdout.write(f"\033]0;{title}\007")
    except Exception:
        pass
