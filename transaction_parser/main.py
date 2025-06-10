"""
Main entry point for the Transaction Parser system.
Provides convenience functions for backward compatibility.
"""

import os
from .utils.processing import process_notification_data, test_raw_csv_input
from .dictionaries.manager import DictionaryManager
from .patterns.manager import PatternManager


def update_dictionaries_interactively():
    """Interactive function to update categorization dictionaries."""
    manager = DictionaryManager()
    manager.run_interactive_updater()


def manage_regex_patterns_interactively(patterns_file=os.path.join('dictionary', 'regex_patterns.json')):
    """Standalone function to manage regex patterns interactively."""
    pattern_manager = PatternManager(patterns_file)
    pattern_manager.run_interactive_pattern_manager()


# Export main functions for easy access
__all__ = [
    'process_notification_data',
    'test_raw_csv_input', 
    'update_dictionaries_interactively',
    'manage_regex_patterns_interactively'
]