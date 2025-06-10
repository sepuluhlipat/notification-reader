"""
Regex pattern loading and management.
"""

import json
import os


class RegexPatternLoader:
    """Handles loading and managing regex patterns from JSON file."""
    
    def __init__(self, patterns_file=os.path.join('dictionary', 'regex_patterns.json')):
        self.patterns_file = patterns_file
        self.patterns = {}
        self._load_patterns()
    
    def _load_patterns(self):
        """Load regex patterns from JSON file."""
        try:
            # Try to load from the same directory as this script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            patterns_path = os.path.join(current_dir, '..', self.patterns_file)
            
            if os.path.exists(patterns_path):
                with open(patterns_path, 'r', encoding='utf-8') as f:
                    self.patterns = json.load(f)
            else:
                # Fallback to current working directory
                if os.path.exists(self.patterns_file):
                    with open(self.patterns_file, 'r', encoding='utf-8') as f:
                        self.patterns = json.load(f)
                else:
                    # Create default patterns if file doesn't exist
                    self._create_default_patterns()
                    self._save_patterns()
                    
        except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
            print(f"Warning: Could not load regex patterns from {self.patterns_file}: {e}")
            print("Using default patterns...")
            self._create_default_patterns()
    
    def _create_default_patterns(self):
        """Create default regex patterns if file doesn't exist."""
        self.patterns = {
            "amount_patterns": [
                r'(?:Rp|IDR)\s*(\d+(?:[.,]\d+)*)',
                r'(\d+(?:[.,]\d+)*)\s*(?:rupiah|rupi)',
                r'(?:received|sent|paid|payment|transfer|top.up|topup|refund|cashback)\s+(?:of\s+)?(?:Rp|IDR)?\s*(\d+(?:[.,]\d+)*)',
                r'(\d+)\s+(?:GoPay Coins|Coins)',
                r'(\d+(?:[.,]\d+)*)'
            ],
            "account_patterns": [
                r'account\s+(?:number|#)?\s*[:\.]?\s*(\d+)',
                r'card\s+(?:number|#)?\s*[:\.]?\s*[*xX]+(\d{4})',
                r'(?:account|card)\s+ending\s+(?:in|with)\s+(\d{4})'
            ],
            "special_patterns": {
                "gopay_coins": r'\d+\s+(?:GoPay Coins|Coins)'
            }
        }
    
    def _save_patterns(self):
        """Save current patterns to JSON file."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            patterns_path = os.path.join(current_dir, '..', self.patterns_file)
            
            with open(patterns_path, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save patterns to {self.patterns_file}: {e}")
    
    def get_amount_patterns(self):
        """Get amount extraction patterns."""
        return self.patterns.get('amount_patterns', [])
    
    def get_account_patterns(self):
        """Get account number extraction patterns."""
        return self.patterns.get('account_patterns', [])
    
    def get_special_pattern(self, pattern_name):
        """Get a specific special pattern."""
        return self.patterns.get('special_patterns', {}).get(pattern_name, '')
    
    def add_amount_pattern(self, pattern):
        """Add a new amount pattern."""
        if 'amount_patterns' not in self.patterns:
            self.patterns['amount_patterns'] = []
        if pattern not in self.patterns['amount_patterns']:
            self.patterns['amount_patterns'].append(pattern)
            self._save_patterns()
            return True
        return False
    
    def add_account_pattern(self, pattern):
        """Add a new account pattern."""
        if 'account_patterns' not in self.patterns:
            self.patterns['account_patterns'] = []
        if pattern not in self.patterns['account_patterns']:
            self.patterns['account_patterns'].append(pattern)
            self._save_patterns()
            return True
        return False
    
    def remove_amount_pattern(self, pattern):
        """Remove an amount pattern."""
        if 'amount_patterns' in self.patterns and pattern in self.patterns['amount_patterns']:
            self.patterns['amount_patterns'].remove(pattern)
            self._save_patterns()
            return True
        return False
    
    def remove_account_pattern(self, pattern):
        """Remove an account pattern."""
        if 'account_patterns' in self.patterns and pattern in self.patterns['account_patterns']:
            self.patterns['account_patterns'].remove(pattern)
            self._save_patterns()
            return True
        return False
    
    def reload_patterns(self):
        """Reload patterns from file."""
        self._load_patterns()