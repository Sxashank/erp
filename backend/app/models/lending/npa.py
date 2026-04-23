"""
NPA (Non-Performing Asset) models re-export.
This module provides compatibility aliases for NPA-related models.
"""

from app.models.lending.collections import NPARecord

# Alias for backward compatibility
NPAClassification = NPARecord

__all__ = ["NPAClassification", "NPARecord"]
