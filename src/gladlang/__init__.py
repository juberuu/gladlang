"""GladLang public API – exposes the run() function, global scope factory, and version."""

from .core.util import run, get_fresh_global_scope
from .version import __version__

__all__ = ["run", "get_fresh_global_scope", "__version__"]
