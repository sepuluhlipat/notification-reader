"""
Dictionary management module for transaction categorization.

This module provides utilities for managing and updating dictionaries
used in transaction categorization, including categories, merchants,
transaction types, and app blacklists.
"""

from .manager import DictionaryManager
from .updater import DictionaryUpdater

__all__ = ['DictionaryManager', 'DictionaryUpdater']