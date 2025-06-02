"""
Categories for transaction classification using unified dictionary structure.
This module loads all dictionaries from a single JSON file.
Removes persona-based categorization - uses only general categories.
"""
import json
import os

# Define the path to the unified JSON file
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_DICTIONARY_FILE = os.path.join(_CURRENT_DIR, 'dictionary.json')

def _load_json_file(file_path):
    """
    Helper function to load data from the unified JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        dict: Data loaded from the JSON file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        print(f"Error loading dictionary from {file_path}. Using default dictionary.")
        return _default_dictionary

# Default unified dictionary structure
_default_dictionary = {
    "categories": {
        "food": ["food", "meal", "restaurant", "order", "menu", "eat", "lunch", "dinner", "breakfast", "gofood", "groceries", "dining"],
        "transport": ["ride", "trip", "gocar", "grab", "transport", "travel", "driver", "gojek ride", "blue bird", "taxi", "fuel", "bus", "transit"],
        "shopping": ["purchase", "buy", "shopping", "shop", "amazon", "store", "item", "product", "tokopedia", "shopee", "lazada"],
        "entertainment": ["movie", "ticket", "entertainment", "game", "music", "streaming", "netflix", "spotify"],
        "bills": ["bill", "utility", "electricity", "water", "internet", "phone", "subscription"],
        "transfer": ["transfer", "send money", "receive money"],
        "finance": ["gopay", "payment", "wallet", "jenius", "bank", "credit", "debit", "card", "saving", "investment", "insurance"],
        "education": ["course", "class", "learning", "tuition", "school", "university", "books", "textbooks"],
        "health": ["medicine", "doctor", "hospital", "health", "medical", "pharmacy", "prescription", "gym"]
    },
    "merchants": {
        "transport": ["blue bird", "gojek ride", "grab", "taxi", "uber"],
        "food": ["gofood", "grabfood", "food delivery", "mie gacoan"],
        "shopping": ["tokopedia", "shopee", "lazada", "amazon", "airpay"],
        "finance": ["gopay", "jenius"]
    },
    "transaction_types": {
        "income": ["received", "receive", "refund", "cashback", "payment from", "transfer from", "credit", "deposit", "bonus", "salary", "reimbursement"],
        "expense": ["paid", "payment to", "sent", "pay", "purchase", "bought", "deducted", "bought", "charged", "payment for", "subscription fee"],
        "transfer": ["transfer", "send to", "sent to", "moved", "moving funds", "fund transfer"],
        "top_up": ["top-up", "top up", "topup", "topped up", "reload", "reload balance", "add money", "added to wallet"]
    },
    "blacklist": []
}

# Load unified dictionary from JSON file with fallback to defaults
_DICTIONARY = _load_json_file(_DICTIONARY_FILE)

def get_categories():
    """
    Get the category dictionary.
    
    Returns:
        dict: Category dictionary
    """
    return _DICTIONARY.get("categories", {})

def get_merchants():
    """
    Get the merchant category dictionary.
    
    Returns:
        dict: Merchant category dictionary
    """
    return _DICTIONARY.get("merchants", {})

def get_transaction_types():
    """
    Get the transaction types dictionary.
    
    Returns:
        dict: Transaction types dictionary
    """
    return _DICTIONARY.get("transaction_types", {})

def get_blacklist():
    """
    Get the blacklist.
    
    Returns:
        list: Blacklisted apps list
    """
    return _DICTIONARY.get("blacklist", [])

def get_all_dictionaries():
    """
    Get the complete unified dictionary structure.
    
    Returns:
        dict: Complete unified dictionary
    """
    return _DICTIONARY

def reload_dictionaries():
    """
    Reload all dictionaries from the unified JSON file.
    Useful for updating the dictionaries without restarting the application.
    
    Returns:
        dict: Statistics about loaded dictionaries
    """
    global _DICTIONARY
    _DICTIONARY = _load_json_file(_DICTIONARY_FILE)

    # Calculate statistics
    categories = get_categories()
    merchants = get_merchants()
    transaction_types = get_transaction_types()
    blacklist = get_blacklist()
    
    categories_keywords = sum(len(keywords) for keywords in categories.values()) if categories else 0
    merchants_keywords = sum(len(keywords) for keywords in merchants.values()) if merchants else 0
    transaction_types_keywords = sum(len(keywords) for keywords in transaction_types.values()) if transaction_types else 0
    blacklist_count = len(blacklist) if isinstance(blacklist, list) else 0
    
    return {
        "categories": {
            "subcategories": len(categories),
            "total_keywords": categories_keywords
        },
        "merchants": {
            "subcategories": len(merchants),
            "total_keywords": merchants_keywords
        },
        "transaction_types": {
            "subcategories": len(transaction_types),
            "total_keywords": transaction_types_keywords
        },
        "blacklist": {
            "total_apps": blacklist_count
        }
    }

# Backward compatibility functions (deprecated - use the new functions above)
def get_categories_for_persona(persona="general"):
    """
    DEPRECATED: Get categories (persona parameter is ignored).
    Use get_categories() instead.
    
    Args:
        persona (str): Ignored - kept for backward compatibility
        
    Returns:
        dict: Category dictionary
    """
    return get_categories()

def get_all_categories():
    """
    DEPRECATED: Use get_categories() instead.
    
    Returns:
        dict: Category dictionary
    """
    return get_categories()