"""
Deprecated compatibility module for pysomweb.

This module provides backward compatibility for code using the old 'somweb' name.
All functionality has been moved to 'pysomweb'. Please update your imports.
"""
from __future__ import annotations

import warnings

# Re-export the new package
from pysomweb import *  # noqa: F401,F403

# If pysomweb defines __all__, reuse it so dir(somweb) looks similar
try:
    from pysomweb import __all__ as __all__  # type: ignore[assignment]
except Exception:  # pragma: no cover
    __all__ = [name for name in globals() if not name.startswith("_")]

warnings.warn(
    "The 'somweb' package has been renamed to 'pysomweb'. "
    "Please update your imports to 'pysomweb' before the next major release.",
    DeprecationWarning,
    stacklevel=2,
)
