"""Compatibility import for IIF rule helpers.

New code should import from ``app.core.iif_rules`` so schemas do not import
the service package and create circular imports.
"""

from app.core.iif_rules import *  # noqa: F401,F403
