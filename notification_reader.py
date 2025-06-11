import numpy as np
import pandas as pd
from datetime import datetime
import re
import json
import os
from enum import Enum
import io


class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    TOP_UP = "top_up"
    UNKNOWN = "unknown"


class Transaction:
    def __init__(self, id=None, timestamp=None):
        self.id = id
        self.timestamp = timestamp or datetime.now().isoformat()
        self.transaction_type = TransactionType.UNKNOWN
        self.amount = None
        self.account_number = None
        self.category = None
    
    def to_dict(self):
        """Convert transaction to dictionary with proper category defaults."""
        default_categories = {
            TransactionType.INCOME: "other",
            TransactionType.EXPENSE: "other", 
            TransactionType.TRANSFER: "general",
            TransactionType.TOP_UP: "finance"
        }
        
        final_category = self.category
        if not final_category and self.transaction_type != TransactionType.UNKNOWN:
            final_category = default_categories.get(self.transaction_type)
        
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "transaction_type": self.transaction_type.value,
            "amount": self.amount,
            "account_number": self.account_number,
            "category": final_category,
        }


class DictionaryLoader:
    """Handles loading dictionaries from JSON file."""
    
    def __init__(self, dictionary_file):
        self.dictionary_file = dictionary_file
        self.dictionary_data = {}
        self._load_dictionary()
    
    def _load_dictionary(self):
        """Load dictionary from JSON file."""
        if not os.path.exists(self.dictionary_file):
            raise FileNotFoundError(f"Dictionary file not found: {self.dictionary_file}")
        
        try:
            with open(self.dictionary_file, 'r', encoding='utf-8') as f:
                self.dictionary_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in dictionary file {self.dictionary_file}: {e}")
        except IOError as e:
            raise IOError(f"Could not read dictionary file {self.dictionary_file}: {e}")
    
    def get_categories(self):
        """Get categories dictionary."""
        if 'categories' not in self.dictionary_data:
            raise KeyError("'categories' not found in dictionary file")
        return self.dictionary_data['categories']
    
    def get_merchants(self):
        """Get merchants dictionary."""
        if 'merchants' not in self.dictionary_data:
            raise KeyError("'merchants' not found in dictionary file")
        return self.dictionary_data['merchants']
    
    def get_transaction_types(self):
        """Get transaction types dictionary."""
        if 'transaction_types' not in self.dictionary_data:
            raise KeyError("'transaction_types' not found in dictionary file")
        return self.dictionary_data['transaction_types']
    
    def get_blacklist(self):
        """Get blacklist from dictionary."""
        if 'blacklist' not in self.dictionary_data:
            raise KeyError("'blacklist' not found in dictionary file")
        return self.dictionary_data['blacklist']


class RegexPatternLoader:
    """Handles loading and managing regex patterns from JSON file."""
    
    def __init__(self, patterns_file):
        self.patterns_file = patterns_file
        self.patterns = {}
        self._load_patterns()
    
    def _load_patterns(self):
        """Load regex patterns from JSON file."""
        if not os.path.exists(self.patterns_file):
            raise FileNotFoundError(f"Regex patterns file not found: {self.patterns_file}")
        
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                self.patterns = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in regex patterns file {self.patterns_file}: {e}")
        except IOError as e:
            raise IOError(f"Could not read regex patterns file {self.patterns_file}: {e}")
        
        # Validate required pattern structure
        required_keys = ['amount_patterns', 'account_patterns', 'special_patterns']
        for key in required_keys:
            if key not in self.patterns:
                raise KeyError(f"Required key '{key}' not found in regex patterns file")
    
    def get_amount_patterns(self):
        """Get amount extraction patterns."""
        return self.patterns.get('amount_patterns', [])
    
    def get_account_patterns(self):
        """Get account number extraction patterns."""
        return self.patterns.get('account_patterns', [])
    
    def get_special_pattern(self, pattern_name):
        """Get a specific special pattern."""
        return self.patterns.get('special_patterns', {}).get(pattern_name, '')


class NotificationParser:
    def __init__(self, dictionary_file, patterns_file):
        """Initialize parser with dictionary and regex patterns from files."""
        self.dictionary_loader = DictionaryLoader(dictionary_file)
        self.pattern_loader = RegexPatternLoader(patterns_file)
        self._load_dictionaries()
        self._compile_patterns()
    
    def _load_dictionaries(self):
        """Load all required dictionaries."""
        self.categories = self.dictionary_loader.get_categories()
        self.merchants = self.dictionary_loader.get_merchants()
        self.transaction_types = self.dictionary_loader.get_transaction_types()
        self.blacklisted_apps = self.dictionary_loader.get_blacklist()
    
    def _compile_patterns(self):
        """Load regex patterns from the pattern loader."""
        self.amount_patterns = self.pattern_loader.get_amount_patterns()
        self.account_patterns = self.pattern_loader.get_account_patterns()
        self.gopay_coins_pattern = self.pattern_loader.get_special_pattern('gopay_coins')
    
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


class BlacklistError(Exception):
    """Exception raised when processing blacklisted apps."""
    def __init__(self, app_name):
        self.app_name = app_name
        super().__init__(f"App '{app_name}' is blacklisted and cannot be processed")


def process_notification_data(df, dictionary_file, patterns_file):
    """Process notifications dataframe to extract structured transaction data."""
    parser = NotificationParser(dictionary_file, patterns_file)
    results = []
    blacklisted_count = 0
    
    for _, row in df.iterrows():
        try:
            message = str(row.get('MESSAGE', '')) if pd.notna(row.get('MESSAGE')) else ""
            contents = str(row.get('CONTENTS', '')) if pd.notna(row.get('CONTENTS')) else ""
            id_val = str(row.get('ID', 'unknown_id')) if pd.notna(row.get('ID')) else "unknown_id"
            timestamp = row.get('TIMESTAMP') if pd.notna(row.get('TIMESTAMP')) else None
            app_name = str(row.get('APP LABEL', '')) if pd.notna(row.get('APP LABEL')) else ""
            
            transaction = parser.parse_notification(message, contents, id_val, timestamp, app_name)
            results.append(transaction.to_dict())
        
        except BlacklistError as e:
            blacklisted_count += 1
            continue
        except Exception as e:
            print(f"Error processing row: {e}")
            continue
        
    print(f"Processed {len(results)} transactions, skipped {blacklisted_count} blacklisted apps")
    return pd.DataFrame(results)


def test_raw_csv_input(raw_input, dictionary_file, patterns_file):
    """Test notifications using raw CSV input without headers."""
    try:
        column_names = ['ID', 'PACKAGE NAME', 'APP LABEL', 'MESSAGE', 'DATE', 'CONTENTS', 'TIMESTAMP']
        
        if '\n' not in raw_input:
            raw_input += '\n'
            
        df = pd.read_csv(io.StringIO(raw_input), names=column_names, header=None)
        result_df = process_notification_data(df, dictionary_file, patterns_file)
        
        return [row.to_dict() for _, row in result_df.iterrows()]
        
    except Exception as e:
        return [{"error": f"Failed to parse CSV: {str(e)}"}]