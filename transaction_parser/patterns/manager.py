"""
Interactive regex pattern management.
"""

import re
import os
from .loader import RegexPatternLoader


class PatternManager:
    """Manages regex patterns with a clean interface."""
    
    def __init__(self, patterns_file=os.path.join('dictionary', 'regex_patterns.json')):
        self.pattern_loader = RegexPatternLoader(patterns_file)
    
    def run_interactive_pattern_manager(self):
        """Interactive pattern management."""
        print("\n" + "=" * 50)
        print("REGEX PATTERN MANAGER")
        print("Manage regex patterns for transaction parsing")
        
        while True:
            choice = self._get_main_menu_choice()
            
            if choice == "1":
                self._manage_amount_patterns()
            elif choice == "2":
                self._manage_account_patterns()
            elif choice == "3":
                self._view_all_patterns()
            elif choice == "4":
                self._test_patterns()
            elif choice == "5":
                print("\nReloading patterns from file...")
                self.pattern_loader.reload_patterns()
                print("Patterns reloaded successfully.")
            elif choice == "6":
                print("\nExiting pattern manager.")
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def _get_main_menu_choice(self):
        """Display main menu and get user choice."""
        print("\n" + "=" * 50)
        print("PATTERN MANAGER MENU")
        print("1. Manage Amount Patterns")
        print("2. Manage Account Patterns")
        print("3. View All Patterns")
        print("4. Test Patterns")
        print("5. Reload Patterns from File")
        print("6. Exit")
        return input("\nEnter your choice [1-6]: ").strip()
    
    def _manage_amount_patterns(self):
        """Manage amount extraction patterns."""
        while True:
            patterns = self.pattern_loader.get_amount_patterns()
            choice = self._get_pattern_menu_choice("Amount", patterns)
            
            if choice == "1":
                self._add_pattern("amount")
            elif choice == "2":
                if patterns:
                    self._remove_pattern("amount", patterns)
            elif choice == "3":
                self._view_patterns("Amount", patterns)
            elif choice == "4":
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def _manage_account_patterns(self):
        """Manage account extraction patterns."""
        while True:
            patterns = self.pattern_loader.get_account_patterns()
            choice = self._get_pattern_menu_choice("Account", patterns)
            
            if choice == "1":
                self._add_pattern("account")
            elif choice == "2":
                if patterns:
                    self._remove_pattern("account", patterns)
            elif choice == "3":
                self._view_patterns("Account", patterns)
            elif choice == "4":
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def _get_pattern_menu_choice(self, pattern_type, patterns):
        """Display pattern menu."""
        print(f"\n{'=' * 50}")
        print(f"MANAGE {pattern_type.upper()} PATTERNS")
        print(f"\nCurrent {pattern_type.lower()} patterns: {len(patterns)}")
        
        print("\nOPTIONS:")
        print("1. Add Pattern")
        print("2. Remove Pattern")
        print("3. View Patterns")
        print("4. Back to Main Menu")
        
        return input("\nEnter your choice [1-4]: ").strip()
    
    def _add_pattern(self, pattern_type):
        """Add a new pattern."""
        pattern = input(f"\nEnter new {pattern_type} pattern (regex): ").strip()
        
        if not pattern:
            print("Pattern cannot be empty.")
            return
        
        # Test if the pattern is valid
        try:
            re.compile(pattern)
        except re.error as e:
            print(f"Invalid regex pattern: {e}")
            return
        
        if pattern_type == "amount":
            success = self.pattern_loader.add_amount_pattern(pattern)
        else:  # account
            success = self.pattern_loader.add_account_pattern(pattern)
        
        if success:
            print(f"{pattern_type.capitalize()} pattern added successfully.")
        else:
            print(f"{pattern_type.capitalize()} pattern already exists.")
    
    def _remove_pattern(self, pattern_type, patterns):
        """Remove a pattern."""
        print(f"\n{pattern_type.capitalize()} patterns:")
        for i, pattern in enumerate(patterns, 1):
            print(f"{i}. {pattern}")
        
        try:
            choice = input(f"\nSelect pattern to remove (1-{len(patterns)}) or Enter to cancel: ").strip()
            if not choice:
                return
            
            idx = int(choice) - 1
            if 0 <= idx < len(patterns):
                pattern = patterns[idx]
                if pattern_type == "amount":
                    success = self.pattern_loader.remove_amount_pattern(pattern)
                else:  # account
                    success = self.pattern_loader.remove_account_pattern(pattern)
                
                if success:
                    print(f"{pattern_type.capitalize()} pattern removed successfully.")
                else:
                    print(f"Failed to remove {pattern_type} pattern.")
            else:
                print("Invalid pattern number.")
        except ValueError:
            print("Please enter a valid number.")
    
    def _view_patterns(self, pattern_type, patterns):
        """View all patterns of a type."""
        print(f"\n{pattern_type.upper()} PATTERNS ({len(patterns)} total):")
        print("=" * 50)
        for i, pattern in enumerate(patterns, 1):
            print(f"{i}. {pattern}")
        
        input("\nPress Enter to continue...")
    
    def _view_all_patterns(self):
        """View all patterns."""
        print("\n" + "=" * 50)
        print("ALL REGEX PATTERNS")
        print("=" * 50)
        
        amount_patterns = self.pattern_loader.get_amount_patterns()
        account_patterns = self.pattern_loader.get_account_patterns()
        gopay_pattern = self.pattern_loader.get_special_pattern('gopay_coins')
        
        print(f"\nAMOUNT PATTERNS ({len(amount_patterns)} total):")
        for i, pattern in enumerate(amount_patterns, 1):
            print(f"  {i}. {pattern}")
        
        print(f"\nACCOUNT PATTERNS ({len(account_patterns)} total):")
        for i, pattern in enumerate(account_patterns, 1):
            print(f"  {i}. {pattern}")
        
        print(f"\nSPECIAL PATTERNS:")
        print(f"  GoPay Coins: {gopay_pattern}")
        
        input("\nPress Enter to continue...")
    
    def _test_patterns(self):
        """Test patterns against sample text."""
        print("\n" + "=" * 50)
        print("PATTERN TESTING")
        print("=" * 50)
        
        test_text = input("\nEnter text to test patterns against: ").strip()
        if not test_text:
            return
        
        print(f"\nTesting text: '{test_text}'")
        print("-" * 50)
        
        # Test amount patterns
        amount_patterns = self.pattern_loader.get_amount_patterns()
        print(f"\nAMOUNT PATTERN MATCHES:")
        for i, pattern in enumerate(amount_patterns, 1):
            try:
                match = re.search(pattern, test_text, re.IGNORECASE)
                if match:
                    print(f"  Pattern {i}: MATCH - '{match.group(1)}'")
                else:
                    print(f"  Pattern {i}: No match")
            except re.error as e:
                print(f"  Pattern {i}: ERROR - {e}")
        
        # Test account patterns
        account_patterns = self.pattern_loader.get_account_patterns()
        print(f"\nACCOUNT PATTERN MATCHES:")
        for i, pattern in enumerate(account_patterns, 1):
            try:
                match = re.search(pattern, test_text, re.IGNORECASE)
                if match:
                    print(f"  Pattern {i}: MATCH - '{match.group(1)}'")
                else:
                    print(f"  Pattern {i}: No match")
            except re.error as e:
                print(f"  Pattern {i}: ERROR - {e}")
        
        # Test special patterns
        gopay_pattern = self.pattern_loader.get_special_pattern('gopay_coins')
        if gopay_pattern:
            try:
                match = re.search(gopay_pattern, test_text, re.IGNORECASE)
                print(f"\nGOPAY COINS PATTERN: {'MATCH' if match else 'No match'}")
            except re.error as e:
                print(f"\nGOPAY COINS PATTERN: ERROR - {e}")
        
        input("\nPress Enter to continue...")