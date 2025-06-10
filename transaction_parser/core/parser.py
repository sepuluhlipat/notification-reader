"""
Core notification parsing functionality.
"""

import re
import os
from .models import Transaction, TransactionType, BlacklistError
from ..patterns.loader import RegexPatternLoader
from ..dictionary import dictionary


class NotificationParser:
    def __init__(self, patterns_file=os.path.join('dictionary', 'regex_patterns.json')):
        """Initialize parser with unified dictionaries and regex patterns."""
        self.pattern_loader = RegexPatternLoader(patterns_file)
        self._load_dictionaries()
        self._compile_patterns()
    
    def _load_dictionaries(self):
        """Load all required dictionaries."""
        self.categories = dictionary.get_categories()
        self.merchants = dictionary.get_merchants()
        self.transaction_types = dictionary.get_transaction_types()
        self.blacklisted_apps = dictionary.get_blacklist()
    
    def _compile_patterns(self):
        """Load regex patterns from the pattern loader."""
        self.amount_patterns = self.pattern_loader.get_amount_patterns()
        self.account_patterns = self.pattern_loader.get_account_patterns()
        self.gopay_coins_pattern = self.pattern_loader.get_special_pattern('gopay_coins')
    
    def reload_dictionaries(self):
        """Reload dictionaries (useful after updates)."""
        self._load_dictionaries()
    
    def reload_patterns(self):
        """Reload regex patterns (useful after pattern updates)."""
        self.pattern_loader.reload_patterns()
        self._compile_patterns()
    
    def _extract_with_patterns(self, text, patterns):
        """Generic pattern extraction helper."""
        if not isinstance(text, str):
            return None
            
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{pattern}': {e}")
                continue
        return None
    
    def _clean_amount(self, amount_str):
        """Clean and convert amount string to float."""
        if not amount_str:
            return None
        try:
            cleaned = amount_str.replace(',', '')
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    def extract_amount(self, text):
        """Extract monetary amounts from text."""
        amount_str = self._extract_with_patterns(text, self.amount_patterns)
        return self._clean_amount(amount_str)
    
    def extract_account_number(self, text):
        """Extract account numbers from text."""
        return self._extract_with_patterns(text, self.account_patterns)
    
    def extract_transaction_type(self, text):
        """Determine transaction type based on text content."""
        if not isinstance(text, str):
            return TransactionType.UNKNOWN
            
        text_lower = text.lower()
        
        # Map transaction type strings to enums
        type_mapping = {
            'income': TransactionType.INCOME,
            'expense': TransactionType.EXPENSE,
            'transfer': TransactionType.TRANSFER,
            'top_up': TransactionType.TOP_UP
        }
        
        for trans_type, keywords in self.transaction_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return type_mapping.get(trans_type, TransactionType.UNKNOWN)
        
        return TransactionType.UNKNOWN
    
    def extract_category(self, text):
        """Categorize transactions based on content."""
        if not isinstance(text, str):
            return "other"
            
        text_lower = text.lower()
        
        # First check merchants for more specific categorization
        for category, merchants in self.merchants.items():
            if any(merchant in text_lower for merchant in merchants):
                return category
        
        # Then check general categories
        for category, keywords in self.categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "other"
    
    def parse_notification(self, message, contents, id=None, timestamp=None, app_name=None):
        """Parse notification and extract transaction details."""
        if app_name and self._is_app_blacklisted(app_name):
            raise BlacklistError(app_name)
        
        transaction = Transaction(id, timestamp)
        full_text = f"{message} {contents}"
        
        transaction.transaction_type = self.extract_transaction_type(full_text)
        transaction.amount = self.extract_amount(full_text)
        transaction.account_number = self.extract_account_number(full_text)
        transaction.category = self.extract_category(full_text)
        
        # Handle special case for GoPay Coins using pattern from file
        if self.gopay_coins_pattern and re.search(self.gopay_coins_pattern, full_text):
            transaction.transaction_type = TransactionType.INCOME
            transaction.category = "cashback"
        
        return transaction
    
    def _is_app_blacklisted(self, app_identifier):
        """Check if an app is blacklisted."""
        app_lower = app_identifier.lower().strip()

        for blacklisted_app in self.blacklisted_apps:
            if blacklisted_app.lower() in app_lower or app_lower in blacklisted_app.lower():
                return True
        return False
    
    def get_pattern_loader(self):
        """Get the pattern loader instance for external management."""
        return self.pattern_loader