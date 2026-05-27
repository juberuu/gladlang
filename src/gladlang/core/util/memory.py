"""Memory limit management – sets process memory limits via resource or watchdog thread."""

import sys
import time


def start_memory_watchdog(max_mb):
    try:
        import psutil
        import threading
    except ImportError:
        return

    def watch():
        import os as _os

        proc = psutil.Process(_os.getpid())
        limit = max_mb * 1024 * 1024

        while True:
            if proc.memory_info().rss > limit:
                sys.stderr.write("System Error: Memory Limit Exceeded\n")
                _os._exit(1)

            time.sleep(0.5)

    t = threading.Thread(target=watch, daemon=True)
    t.start()


def set_memory_limit(max_mb):
    try:
        import resource
    except ImportError:
        resource = None

    if resource:
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            limit_bytes = max_mb * 1024 * 1024
            new_soft = (
                min(limit_bytes, hard)
                if hard != resource.RLIM_INFINITY
                else limit_bytes
            )

            resource.setrlimit(resource.RLIMIT_AS, (new_soft, hard))
        except Exception as e:
            sys.stderr.write(f"Warning: Could not set memory limit: {e}\n")
    else:
        start_memory_watchdog(max_mb)
