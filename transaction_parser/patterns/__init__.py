"""
Regex pattern management functionality.

This module provides classes for loading, managing, and testing regex patterns
used in transaction parsing. It includes both programmatic access and 
interactive management tools.
"""

from .loader import RegexPatternLoader
from .manager import PatternManager

__all__ = [
    'RegexPatternLoader',
    'PatternManager'
]