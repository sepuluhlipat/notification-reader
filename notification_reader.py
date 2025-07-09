import numpy as np
import pandas as pd
from datetime import datetime
import re
import json
import os
from enum import Enum


class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    UNKNOWN = "unknown"


class Transaction:
    def __init__(self, id=None, timestamp=None, message_id=None):
        self.id = id
        self.message_id = message_id
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.transaction_type = TransactionType.UNKNOWN
        self.amount = None
        self.account_number = None
        self.category = None
        self.is_promotional = False
    
    def to_dict(self):
        default_categories = {
            TransactionType.INCOME: "miscellaneous",
            TransactionType.EXPENSE: "miscellaneous", 
            TransactionType.TRANSFER: "general"
        }
        
        final_category = self.category or default_categories.get(self.transaction_type, "miscellaneous")
        
        return {
            "id": self.id,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "transaction_type": self.transaction_type.value,
            "amount": self.amount,
            "account_number": self.account_number,
            "category": final_category,
        }


class ConfigLoader:
    def __init__(self, dictionary_file, patterns_file):
        self.dictionary_data = self._load_json(dictionary_file, "Dictionary")
        self.patterns = self._load_json(patterns_file, "Regex patterns")
        self._validate_patterns()
    
    def _load_json(self, file_path, file_type):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{file_type} file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_type.lower()} file {file_path}: {e}")
        except IOError as e:
            raise IOError(f"Could not read {file_type.lower()} file {file_path}: {e}")
    
    def _validate_patterns(self):
        required_keys = ['amount_patterns', 'account_patterns']
        for key in required_keys:
            if key not in self.patterns:
                raise KeyError(f"Required key '{key}' not found in regex patterns file")
    
    def get_dict_data(self, key):
        if key not in self.dictionary_data:
            raise KeyError(f"'{key}' not found in dictionary file")
        return self.dictionary_data[key]
    
    def get_pattern_data(self, key, subkey=None):
        data = self.patterns.get(key, {})
        return data.get(subkey, []) if subkey else data


class NotificationParser:
    def __init__(self, dictionary_file, patterns_file):
        self.config = ConfigLoader(dictionary_file, patterns_file)
        self._load_config()
    
    def _load_config(self):
        self.categories = self.config.get_dict_data('categories')
        self.merchants = self.config.get_dict_data('merchants')
        self.transaction_types = self.config.get_dict_data('transaction_types')
        self.blacklisted_apps = self.config.get_dict_data('blacklist')
        
        # Load allowlist - if not present, default to empty list (process all apps)
        try:
            self.allowlisted_apps = self.config.get_dict_data('allowlist')
        except KeyError:
            self.allowlisted_apps = []
        
        self.amount_patterns = self.config.get_pattern_data('amount_patterns')
        self.account_patterns = self.config.get_pattern_data('account_patterns')
        
        # Load promotional and confirmation patterns from config
        self.promotional_keywords = self.config.get_pattern_data('promotional_patterns', 'keywords')
        self.promotional_regex_patterns = self.config.get_pattern_data('promotional_patterns', 'regex_patterns')
        self.confirmation_keywords = self.config.get_pattern_data('confirmation_patterns', 'keywords')
    
    def _extract_with_patterns(self, text, patterns):
        if not isinstance(text, str) or not patterns:
            return None
            
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{pattern}': {e}")
        return None
    
    def _clean_amount(self, amount_str):
        """
        Clean Indonesian and English currency formats to float.
        Indonesian: periods = thousands, comma = decimal (12.000.000,50)
        English: commas = thousands, period = decimal (12,000,000.50)
        """
        if not amount_str:
            return None
        
        try:
            amount_str = amount_str.strip()
            
            # Indonesian format: comma as decimal separator
            if ',' in amount_str:
                # Find the last comma
                last_comma_idx = amount_str.rfind(',')
                decimal_part = amount_str[last_comma_idx + 1:]
                
                # Valid decimal part: 1-2 digits only
                if len(decimal_part) <= 2 and decimal_part.isdigit():
                    integer_part = amount_str[:last_comma_idx]
                    return float(integer_part.replace('.', '').replace(',', '') + '.' + decimal_part)
            
            # English format: period as decimal separator (at end with 1-2 digits)
            if '.' in amount_str:
                last_period_idx = amount_str.rfind('.')
                decimal_part = amount_str[last_period_idx + 1:]
                
                # Valid decimal part: 1-2 digits only
                if len(decimal_part) <= 2 and decimal_part.isdigit():
                    integer_part = amount_str[:last_period_idx]
                    return float(integer_part.replace(',', '').replace('.', '') + '.' + decimal_part)
            
            # No decimal part: remove all separators
            return float(amount_str.replace('.', '').replace(',', ''))
            
        except (ValueError, AttributeError):
            return None
    
    def _is_promotional_message(self, text):
        if not isinstance(text, str):
            return False
            
        text_lower = text.lower()
        
        # Check promotional regex patterns first
        if self.promotional_regex_patterns:
            for pattern in self.promotional_regex_patterns:
                try:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        return True
                except re.error as e:
                    print(f"Warning: Invalid promotional regex pattern '{pattern}': {e}")
        
        # Count promotional vs confirmation keywords from config
        promotional_score = sum(1 for keyword in self.promotional_keywords if keyword in text_lower)
        confirmation_score = sum(1 for keyword in self.confirmation_keywords if keyword in text_lower)
        
        if promotional_score >= 2:  # Multiple promotional keywords
            return True
    
        if promotional_score > 0 and confirmation_score == 0:  # Only promotional, no confirmation
            return True
        
        return promotional_score > confirmation_score and promotional_score > 0
    
    def extract_amount(self, text):
        amount_str = self._extract_with_patterns(text, self.amount_patterns)
        return self._clean_amount(amount_str)
    
    def extract_account_number(self, text):
        return self._extract_with_patterns(text, self.account_patterns)
    
    def extract_transaction_type(self, text):
        if not isinstance(text, str):
            return TransactionType.UNKNOWN
            
        text_lower = text.lower()
        type_mapping = {
            'income': TransactionType.INCOME,
            'expense': TransactionType.EXPENSE,
            'transfer': TransactionType.TRANSFER
        }
        
        for trans_type, keywords in self.transaction_types.items():
            if trans_type in type_mapping and any(keyword in text_lower for keyword in keywords):
                return type_mapping[trans_type]
        
        return TransactionType.UNKNOWN
    
    def extract_category(self, text):
        if not isinstance(text, str):
            return "miscellaneous"
            
        text_lower = text.lower()
        
        # Check merchants first
        for category, merchants in self.merchants.items():
            if any(merchant in text_lower for merchant in merchants):
                return category
        
        # Check general categories
        for category, keywords in self.categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "miscellaneous"
    
    def _is_app_blacklisted(self, app_identifier):
        if not app_identifier:
            return False
            
        app_lower = app_identifier.lower().strip()
        return any(blacklisted_app.lower() in app_lower or app_lower in blacklisted_app.lower() 
                  for blacklisted_app in self.blacklisted_apps)
    
    def _is_app_allowlisted(self, app_identifier):
        # If allowlist is empty, allow all apps (backward compatibility)
        if not self.allowlisted_apps:
            return True
            
        if not app_identifier:
            return False
            
        app_lower = app_identifier.lower().strip()
        return any(allowlisted_app.lower() in app_lower or app_lower in allowlisted_app.lower() 
                  for allowlisted_app in self.allowlisted_apps)
    
    def parse_notification(self, message, contents, id=None, timestamp=None, app_name=None, message_id=None):
        # Check allowlist first - if app is not allowlisted, raise AllowlistError
        if not self._is_app_allowlisted(app_name):
            raise AllowlistError(app_name)
        
        # Then check blacklist
        if app_name and self._is_app_blacklisted(app_name):
            raise BlacklistError(app_name)
        
        transaction = Transaction(id, timestamp, message_id)
        full_text = f"{message} {contents}"
        
        # Check if promotional first - this takes precedence
        transaction.is_promotional = self._is_promotional_message(full_text)
        
        if transaction.is_promotional:
            transaction.transaction_type = TransactionType.UNKNOWN
            transaction.amount = None
        else:
            transaction.transaction_type = self.extract_transaction_type(full_text)
            transaction.amount = self.extract_amount(full_text)
        
        transaction.account_number = self.extract_account_number(full_text)
        transaction.category = self.extract_category(full_text)
        
        return transaction


class BlacklistError(Exception):
    def __init__(self, app_name):
        self.app_name = app_name
        super().__init__(f"App '{app_name}' is blacklisted and cannot be processed")


class AllowlistError(Exception):
    def __init__(self, app_name):
        self.app_name = app_name
        super().__init__(f"App '{app_name}' is not in allowlist and will be skipped")


def process_notification_data(df, dictionary_file, patterns_file, filter_promotional=True):
    parser = NotificationParser(dictionary_file, patterns_file)
    results = []
    blacklisted_count = 0
    not_allowlisted_count = 0
    promotional_count = 0
    
    for _, row in df.iterrows():
        try:
            message = str(row.get('message', '')) if pd.notna(row.get('message')) else ""
            contents = str(row.get('contents', '')) if pd.notna(row.get('contents')) else ""
            user_id = str(row.get('user_id', 'unknown_id')) if pd.notna(row.get('user_id')) else "unknown_id"
            message_id = str(row.get('id', 'unknown_msg_id')) if pd.notna(row.get('id')) else "unknown_msg_id"
            timestamp = str(row.get('timestamp')) if pd.notna(row.get('timestamp')) else None
            app_name = str(row.get('app_label', '')) if pd.notna(row.get('app_label')) else ""
                        
            transaction = parser.parse_notification(message, contents, user_id, timestamp, app_name, message_id)
            
            # Filter promotional messages and invalid amounts
            if filter_promotional and transaction.is_promotional:
                promotional_count += 1
                continue
                
            if transaction.amount is None or transaction.amount <= 0:
                continue
                
            results.append(transaction.to_dict())
        
        except AllowlistError:
            not_allowlisted_count += 1
        except BlacklistError:
            blacklisted_count += 1
        except Exception as e:
            print(f"Error processing row with message id {row.get('id', 'unknown')}: {e}")
    
    print(f"Processed {len(results)} transactions")
    print(f"Skipped {not_allowlisted_count} apps not in allowlist")
    print(f"Skipped {blacklisted_count} blacklisted apps")
    print(f"Filtered out {promotional_count} promotional messages")
    
    return pd.DataFrame(results)