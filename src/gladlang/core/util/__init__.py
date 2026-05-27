"""Utility functions for runtime – final helpers, binding, global scope, memory, source detachment, REPL helpers, runner, and locking."""

from .final_helpers import is_final_anywhere
from .global_scope import get_fresh_global_scope
from .memory import start_memory_watchdog, set_memory_limit
from .source_detach import detach_value, detach_source_from_node
from .runner import run
from .repl_helpers import strip_double_quoted, is_complete
from .locking import _NoLock

__all__ = [
    "is_final_anywhere",
    "get_fresh_global_scope",
    "start_memory_watchdog",
    "set_memory_limit",
    "detach_value",
    "detach_source_from_node",
    "run",
    "strip_double_quoted",
    "is_complete",
    "_NoLock",
]
