"""
Core transaction parsing functionality.

This module provides the core classes and functionality for parsing
financial transaction notifications.
"""

from .models import Transaction, TransactionType, BlacklistError
from .parser import NotificationParser

__all__ = [
    'Transaction',
    'TransactionType', 
    'BlacklistError',
    'NotificationParser'
]