"""
Transaction Parser - A system for parsing financial notifications and extracting transaction data.

This package provides tools for:
- Parsing financial notifications from various apps
- Extracting transaction details (amount, type, category, etc.)
- Managing categorization dictionaries and regex patterns
- Processing notification data from CSV files

Main Components:
- Core parsing engine with configurable patterns
- Dictionary management for transaction categorization
- Pattern management for regex-based extraction
- Utility functions for data processing

Example Usage:
    >>> from transaction_parser import process_notification_data
    >>> import pandas as pd
    >>> 
    >>> # Process notifications from a DataFrame
    >>> df = pd.read_csv('notifications.csv')
    >>> transactions = process_notification_data(df)
    >>> print(f"Processed {len(transactions)} transactions")
    
    >>> # Interactive dictionary management
    >>> from transaction_parser import update_dictionaries_interactively
    >>> update_dictionaries_interactively()
"""

# Import core functionality
from .utils.processing import process_notification_data, test_raw_csv_input
from .core.models import Transaction, TransactionType
from .core.parser import NotificationParser

# Import management interfaces
from .dictionaries.manager import DictionaryManager
from .patterns.manager import PatternManager

# Import convenience functions from main
from .main import update_dictionaries_interactively, manage_regex_patterns_interactively

# Package metadata
__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "A system for parsing financial notifications and extracting transaction data"

# Main public API
__all__ = [
    # Core classes
    'Transaction',
    'TransactionType', 
    'NotificationParser',
    
    # Processing functions
    'process_notification_data',
    'test_raw_csv_input',
    
    # Management classes
    'DictionaryManager',
    'PatternManager',
    
    # Interactive functions
    'update_dictionaries_interactively',
    'manage_regex_patterns_interactively',
]