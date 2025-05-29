"""
Categories for transaction classification based on user personas.
This module loads predefined category dictionaries from JSON files.
"""
import json
import os

# Define the path to the JSON files
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_CATEGORIES_FILE = os.path.join(_CURRENT_DIR, 'categories.json')
_MERCHANTS_FILE = os.path.join(_CURRENT_DIR, 'merchants.json')
_TRANSACTION_TYPES_FILE = os.path.join(_CURRENT_DIR, 'transaction_types.json')
_BLACKLIST_FILE = os.path.join(_CURRENT_DIR, 'blacklist.json')

def _load_json_file(file_path):
    """
    Helper function to load data from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        dict: Data loaded from the JSON file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        # Fall back to hardcoded defaults if JSON file loading fails
        if 'categories.json' in file_path:
            return _default_categories
        elif 'merchants.json' in file_path:
            return _default_merchants
        elif 'transaction_types.json' in file_path:
            return _default_transaction_types
        elif 'blacklist.json' in file_path:
            return {"blacklisted_apps": []}
        return {}

# Default dictionaries to use as fallbacks if JSON files aren't loaded correctly
_default_categories = {
    "general": {
        "food": ["food", "meal", "restaurant", "order", "menu", "eat", "lunch", "dinner", "breakfast", "gofood", "groceries", "dining"],
        "transport": ["ride", "trip", "gocar", "grab", "transport", "travel", "driver", "gojek ride", "blue bird", "taxi", "fuel", "bus", "transit"],
        "shopping": ["purchase", "buy", "shopping", "shop", "amazon", "store", "item", "product", "tokopedia", "shopee", "lazada"],
        "entertainment": ["movie", "ticket", "entertainment", "game", "music", "streaming", "netflix", "spotify"],
        "bills": ["bill", "utility", "electricity", "water", "internet", "phone", "subscription"],
        "transfer": ["transfer", "send money", "receive money"],
        "finance": ["gopay", "payment", "wallet", "jenius", "bank", "credit", "debit", "card", "saving", "investment", "insurance"],
        "education": ["course", "class", "learning", "tuition", "school", "university", "books", "textbooks"],
        "health": ["medicine", "doctor", "hospital", "health", "medical", "pharmacy", "prescription", "gym"]
    }
}

_default_merchants = {
    "transport": ["blue bird", "gojek ride", "grab", "taxi", "uber"],
    "food": ["gofood", "grabfood", "food delivery", "mie gacoan"],
    "shopping": ["tokopedia", "shopee", "lazada", "amazon", "airpay"],
    "finance": ["gopay", "jenius"]
}

_default_transaction_types = {
    "income": ["received", "receive", "refund", "cashback", "payment from", "transfer from", "credit", "deposit", "bonus", "salary", "reimbursement"],
    "expense": ["paid", "payment to", "sent", "pay", "purchase", "bought", "deducted", "bought", "charged", "payment for", "subscription fee"],
    "transfer": ["transfer", "send to", "sent to", "moved", "moving funds", "fund transfer"],
    "top_up": ["top-up", "top up", "topup", "topped up", "reload", "reload balance", "add money", "added to wallet"]
}

# Load dictionaries from JSON files with fallback to defaults
_CATEGORIES = _load_json_file(_CATEGORIES_FILE)
_MERCHANTS = _load_json_file(_MERCHANTS_FILE)
_TRANSACTION_TYPES = _load_json_file(_TRANSACTION_TYPES_FILE)
_BLACKLIST = _load_json_file(_BLACKLIST_FILE)

def get_categories_for_persona(persona="general"):
    """
    Get the category dictionary for the specified persona.
    
    Args:
        persona (str): User persona (student, young professional, etc.)
        
    Returns:
        dict: Category dictionary for the specified persona
    """
    persona_key = persona.strip().lower()
    return _CATEGORIES.get(persona_key, _CATEGORIES.get("general", {}))

def get_merchants():
    """
    Get the merchant category dictionary.
    
    Returns:
        dict: Merchant category dictionary
    """
    return _MERCHANTS

def get_transaction_types():
    """
    Get the transaction types dictionary.
    
    Returns:
        dict: Transaction types dictionary
    """
    return _TRANSACTION_TYPES

def get_all_categories():
    """
    Get the complete categories dictionary.
    
    Returns:
        dict: Complete categories dictionary
    """
    return _CATEGORIES

def get_blacklist():
    """
    Get the blacklist dictionary.
    
    Returns:
        dict: Blacklist dictionary
    """    
    return _BLACKLIST

def reload_dictionaries():
    """
    Reload all dictionaries from their JSON files.
    Useful for updating the dictionaries without restarting the application.
    """
    global _CATEGORIES, _MERCHANTS, _TRANSACTION_TYPES, _BLACKLIST
    _CATEGORIES = _load_json_file(_CATEGORIES_FILE)
    _MERCHANTS = _load_json_file(_MERCHANTS_FILE)
    _TRANSACTION_TYPES = _load_json_file(_TRANSACTION_TYPES_FILE)
    _BLACKLIST = _load_json_file(_BLACKLIST_FILE)
    
    blacklist_data = get_blacklist()
    blacklist_count = len(blacklist_data) if blacklist_data else 0
    
    return {
        "categories": len(_CATEGORIES),
        "merchants": len(_MERCHANTS),
        "transaction_types": len(_TRANSACTION_TYPES),
        "blacklist": blacklist_count
    }