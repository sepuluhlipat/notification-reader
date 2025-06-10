"""
Core transaction models and enums.
"""

from enum import Enum
from datetime import datetime


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


class BlacklistError(Exception):
    """Exception raised when processing blacklisted apps."""
    def __init__(self, app_name):
        self.app_name = app_name
        super().__init__(f"App '{app_name}' is blacklisted and cannot be processed")