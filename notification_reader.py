import numpy as np
import pandas as pd
from datetime import datetime
import re
from enum import Enum
import io
import dictionary.dictionary as dictionary
from dictionary.dictionary_updater import DictionaryUpdater


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
        self.from_account = None
        self.to_account = None
        self.balance = None
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
            
        account = None
        if self.transaction_type == TransactionType.INCOME:
            account = self.to_account or 'GoPay'
        elif self.transaction_type == TransactionType.EXPENSE:
            account = self.from_account or 'GoPay'
        elif self.transaction_type == TransactionType.TRANSFER:
            if self.from_account and self.to_account:
                account = f"{self.from_account} -> {self.to_account}"
            else:
                account = self.from_account or self.to_account or 'GoPay'
        else:
            account = self.from_account or self.to_account or 'GoPay'
        
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "transaction_type": self.transaction_type.value,
            "amount": self.amount,
            "account": account, 
            "category": final_category,
        }


class NotificationParser:
    def __init__(self, persona="general"):
        """Initialize parser with persona-specific categories."""
        self.persona = persona.strip().lower()
        self._load_dictionaries()
        self._compile_patterns()
    
    def _load_dictionaries(self):
        """Load all required dictionaries."""
        self.categories = dictionary.get_categories_for_persona(self.persona)
        self.merchants = dictionary.get_merchants()
        self.transaction_types = dictionary.get_transaction_types()
    
    def _compile_patterns(self):
        """Compile regex patterns for transaction extraction."""
        self.amount_patterns = [
            r'(?:Rp|IDR)\s*(\d+(?:[.,]\d+)*)',
            r'(\d+(?:[.,]\d+)*)\s*(?:rupiah|rupi)',
            r'(?:received|sent|paid|payment|transfer|top.up|topup|refund|cashback|balance)\s+(?:of\s+)?(?:Rp|IDR)?\s*(\d+(?:[.,]\d+)*)',
            r'(\d+)\s+(?:GoPay Coins|Coins)',
            r'(\d+(?:[.,]\d+)*)'
        ]
        
        self.balance_patterns = [
            r'(?:balance|saldo)(?:\s+is|\s+now|\s+remaining|\:)?\s+(?:Rp|IDR)?\s*(\d+(?:[.,]\d+)*)',
            r'(?:available|remaining)\s+(?:balance|saldo)(?:\s+is|\:)?\s+(?:Rp|IDR)?\s*(\d+(?:[.,]\d+)*)',
            r'(?:you\s+have|your)\s+(?:balance|saldo)(?:\s+is|\:)?\s+(?:Rp|IDR)?\s*(\d+(?:[.,]\d+)*)'
        ]
        
        self.account_patterns = [
            r'account\s+(?:number|#)?\s*[:\.]?\s*(\d+)',
            r'card\s+(?:number|#)?\s*[:\.]?\s*[*xX]+(\d{4})',
            r'(?:account|card)\s+ending\s+(?:in|with)\s+(\d{4})'
        ]
        
        self.from_account_patterns = [
            r'from\s+(?:account)?\s*(?:number)?\s*[:\.]?\s*([\w\s]+?)(?:\.|\s*$)',
            r'([\w\s]+?)\s+sent\s+you',
            r'received\s+from\s+([\w\s]+?)(?:\.|\s*$)',
            r'from\s+your\s+([\w\s]+?)(?:\.|\s*$)'
        ]
        
        self.to_account_patterns = [
            r'to\s+(?:account)?\s*(?:number)?\s*[:\.]?\s*([\w\s\-&\']+?)(?:\.|\s*$|\s+for|\s+on|\s+at|\s+with)',
            r'sent\s+to\s+([\w\s\-&\']+?)(?:\.|\s*$|\s+for|\s+on|\s+at|\s+with)',
            r'paid\s+to\s+([\w\s\-&\']+?)(?:\.|\s*$|\s+for|\s+on|\s+at|\s+with)',
            r'payment\s+(?:successfully\s+)?made\s+to\s+([\w\s\-&\']+?)(?:\.|\s*$|\s+for|\s+on|\s+at|\s+with)'
        ]
    
    def set_persona_categories(self, persona):
        """Update persona and reload categories."""
        self.persona = persona.strip().lower()
        self.categories = dictionary.get_categories_for_persona(self.persona)
    
    def _extract_with_patterns(self, text, patterns):
        """Generic pattern extraction helper."""
        if not isinstance(text, str):
            return None
            
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _clean_amount(self, amount_str):
        """Clean and convert amount string to float."""
        if not amount_str:
            return None
        try:
            cleaned = amount_str.replace('.', '').replace(',', '.')
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    def extract_amount(self, text):
        """Extract monetary amounts from text."""
        amount_str = self._extract_with_patterns(text, self.amount_patterns)
        return self._clean_amount(amount_str)
    
    def extract_balance(self, text):
        """Extract balance information from text."""
        balance_str = self._extract_with_patterns(text, self.balance_patterns)
        return self._clean_amount(balance_str)
    
    def extract_account_number(self, text):
        """Extract account numbers from text."""
        return self._extract_with_patterns(text, self.account_patterns)
    
    def extract_from_account(self, text):
        """Extract sender account information."""
        result = self._extract_with_patterns(text, self.from_account_patterns)
        return result.strip() if result else None
    
    def extract_to_account(self, text):
        """Extract recipient account information."""
        result = self._extract_with_patterns(text, self.to_account_patterns)
        if result:
            return result.strip().rstrip('.')
        return None
    
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
        """Categorize transactions based on content and persona."""
        if not isinstance(text, str):
            return "other"
            
        text_lower = text.lower()
        
        for category, merchants in self.merchants.items():
            if any(merchant in text_lower for merchant in merchants):
                return category
        
        for category, keywords in self.categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "other"
    
    def _apply_default_accounts(self, transaction):
        """Apply default account values based on transaction type."""
        if transaction.transaction_type == TransactionType.INCOME and not transaction.to_account:
            transaction.to_account = 'GoPay'
        elif transaction.transaction_type == TransactionType.EXPENSE and not transaction.from_account:
            transaction.from_account = 'GoPay'
    
    def _categorize_by_merchant(self, transaction, text):
        """Categorize transaction based on merchant information."""
        if transaction.to_account:
            to_account_lower = transaction.to_account.lower()
            for category, merchants in self.merchants.items():
                if any(merchant in to_account_lower for merchant in merchants):
                    return category
        
        return self.extract_category(text)
    
    def parse_notification(self, message, contents, id=None, timestamp=None, app_name=None):
        """Parse notification and extract transaction details."""
        if app_name and self._is_app_blacklisted(app_name):
            raise BlacklistError(app_name)
        
        transaction = Transaction(id, timestamp)
        full_text = f"{message} {contents}"
        
        transaction.transaction_type = self.extract_transaction_type(full_text)
        transaction.amount = self.extract_amount(full_text)
        transaction.account_number = self.extract_account_number(full_text)
        transaction.from_account = self.extract_from_account(full_text)
        transaction.to_account = self.extract_to_account(full_text)
        transaction.balance = self.extract_balance(full_text)
        
        # Handle special case for GoPay Coins
        if re.search(r'\d+\s+(?:GoPay Coins|Coins)', full_text):
            transaction.transaction_type = TransactionType.INCOME
            transaction.category = "cashback"
        
        self._apply_default_accounts(transaction)
        
        if not transaction.category:
            transaction.category = self._categorize_by_merchant(transaction, full_text)
        
        return transaction
    
    def _is_app_blacklisted(self, app_identifier):
        """Check if an app is blacklisted."""
        blacklisted_apps = dictionary.get_blacklist()
        app_lower = app_identifier.lower().strip()

        for blacklisted_app in blacklisted_apps:
            if blacklisted_app.lower() in app_lower or app_lower in blacklisted_app.lower():
                return True
        return False


def process_notification_data(df, persona="general"):
    """Process notifications dataframe to extract structured transaction data."""
    parser = NotificationParser(persona)
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


def test_raw_csv_input(raw_input, persona="general"):
    """Test notifications using raw CSV input without headers."""
    try:
        column_names = ['ID', 'PACKAGE NAME', 'APP LABEL', 'MESSAGE', 'DATE', 'CONTENTS', 'TIMESTAMP']
        
        if '\n' not in raw_input:
            raw_input += '\n'
            
        df = pd.read_csv(io.StringIO(raw_input), names=column_names, header=None)
        result_df = process_notification_data(df, persona)
        
        return [row.to_dict() for _, row in result_df.iterrows()]
        
    except Exception as e:
        return [{"error": f"Failed to parse CSV: {str(e)}"}]


class DictionaryManager:
    """Manages dictionary updates with a cleaner interface."""
    
    def __init__(self):
        self.updater = DictionaryUpdater(dictionary)
    
    def run_interactive_updater(self):
        """Main interactive dictionary updater."""
        print("\n" + "=" * 50)
        print("DICTIONARY UPDATER")
        print("Update transaction categorization dictionaries")
        
        while True:
            choice = self._get_main_menu_choice()
            
            if choice == "1":
                if not self._update_categories():
                    break
            elif choice == "2":
                if not self._update_dictionary("merchants"):
                    break
            elif choice == "3":
                if not self._update_dictionary("transaction_types"):
                    break
            elif choice == "4":
                if not self._update_blacklist():
                    break
            elif choice == "5":
                print("\nExiting dictionary updater.")
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def _get_main_menu_choice(self):
        """Display main menu and get user choice."""
        print("\n" + "=" * 50)
        print("SELECT DICTIONARY TO UPDATE")
        print("1. Categories")
        print("2. Merchants") 
        print("3. Transaction Types")
        print("4. Blacklisted Apps")
        print("5. Exit")
        return input("\nEnter your choice [1-5]: ").strip()
    
    def _update_categories(self):
        """Handle category updates."""
        while True:
            personas = self.updater.get_subcategories("categories")
            choice = self._get_categories_menu_choice(personas)
            
            if choice == "1":
                self._add_persona()
            elif choice == "2":
                if personas and not self._update_persona(personas):
                    return False
            elif choice == "3":
                if personas:
                    self._remove_persona(personas)
            elif choice == "4":
                return True
            elif choice == "5":
                return False
            else:
                print("\nInvalid choice. Please try again.")
    
    def _get_categories_menu_choice(self, personas):
        """Display categories menu."""
        print("\n" + "=" * 50)
        print("UPDATE CATEGORIES")
        
        if personas:
            print("\nAvailable personas:")
            for i, persona in enumerate(personas, 1):
                print(f"{i}. {persona}")
        
        print("\nOPTIONS:")
        print("1. Add new persona")
        print("2. Update existing persona")
        print("3. Remove a persona")
        print("4. Back to main menu")
        print("5. Exit")
        
        return input("\nEnter your choice [1-5]: ").strip()
    
    def _add_persona(self):
        """Add a new persona."""
        persona_name = input("\nEnter new persona name (or 'exit' to quit): ").strip().lower()
        
        if persona_name == 'exit':
            return False
        
        if not persona_name:
            print("\nPersona name cannot be empty.")
            return True
        
        if self.updater.add_persona(persona_name):
            print(f"\nPersona '{persona_name}' added successfully.")
            
            if self._confirm_action(f"add categories for '{persona_name}'"):
                return self._update_subcategories("categories", persona_name)
        else:
            print(f"\nFailed to add persona '{persona_name}'.")
        
        return True
    
    def _update_persona(self, personas):
        """Update an existing persona."""
        persona_choice = input("\nEnter persona number to update (or 'exit' to quit): ").strip()
        
        if persona_choice.lower() == 'exit':
            return False
        
        try:
            persona_idx = int(persona_choice) - 1
            if 0 <= persona_idx < len(personas):
                persona = personas[persona_idx]
                return self._update_subcategories("categories", persona)
            else:
                print("\nInvalid persona number.")
        except ValueError:
            print("\nPlease enter a valid persona number.")
        
        return True
    
    def _remove_persona(self, personas):
        """Remove a persona."""
        try:
            persona_choice = input("\nSelect persona to remove (number) or Enter to cancel: ").strip()
            if not persona_choice:
                return
            
            persona_idx = int(persona_choice) - 1
            if 0 <= persona_idx < len(personas):
                persona = personas[persona_idx]
                if self._confirm_action(f"remove persona '{persona}'"):
                    if self.updater.remove_persona(persona):
                        print(f"\nPersona '{persona}' removed successfully.")
                        self._save_changes()
        except ValueError:
            print("\nPlease enter a valid persona number.")
    
    def _update_dictionary(self, dict_name):
        """Update merchants or transaction_types dictionary."""
        while True:
            subcategories = self.updater.get_subcategories(dict_name)
            choice = self._get_dictionary_menu_choice(dict_name, subcategories)
            
            if choice == "1":
                self._add_subcategory(dict_name)
            elif choice == "2":
                if subcategories and not self._update_subcategory(dict_name, subcategories):
                    return False
            elif choice == "3":
                if subcategories:
                    self._remove_subcategory(dict_name, subcategories)
            elif choice == "4":
                return True
            elif choice == "5":
                return False
            else:
                print("\nInvalid choice. Please try again.")
    
    def _get_dictionary_menu_choice(self, dict_name, subcategories):
        """Display dictionary update menu."""
        print(f"\n{'=' * 50}")
        print(f"UPDATE {dict_name.upper()}")
        
        if subcategories:
            print(f"\nAvailable {dict_name}:")
            for i, subcat in enumerate(subcategories, 1):
                print(f"{i}. {subcat}")
        
        item_name = dict_name[:-1]  # Remove 's'
        print(f"\nOPTIONS:")
        print(f"1. Add new {item_name}")
        print(f"2. Update existing {item_name}")
        print(f"3. Remove a {item_name}")
        print("4. Back to main menu")
        print("5. Exit")
        
        return input("\nEnter your choice [1-5]: ").strip()
    
    def _add_subcategory(self, dict_name):
        """Add a subcategory to dictionary."""
        item_name = dict_name[:-1]
        subcat_name = input(f"\nEnter new {item_name} name (or 'exit' to quit): ").strip().lower()
        
        if subcat_name == 'exit':
            return False
        
        if not subcat_name:
            print(f"\n{item_name.capitalize()} name cannot be empty.")
            return True
        
        if self.updater.add_subcategory(dict_name, subcat_name):
            print(f"\n{item_name.capitalize()} '{subcat_name}' added successfully.")
            self._add_initial_keywords(dict_name, subcat_name)
            self._save_changes()
        else:
            print(f"\nFailed to add {item_name} '{subcat_name}'.")
        
        return True
    
    def _add_initial_keywords(self, dict_name, subcat_name):
        """Add initial keywords to a subcategory."""
        keywords = input("\nEnter initial keywords (comma-separated) or press Enter to skip: ").strip()
        if keywords:
            for keyword in keywords.split(','):
                keyword = keyword.strip().lower()
                if keyword:
                    self.updater.add_keyword(dict_name, subcat_name, keyword)
    
    def _update_subcategory(self, dict_name, subcategories):
        """Update a subcategory."""
        item_name = dict_name[:-1]
        subcat_choice = input(f"\nEnter {item_name} number to update (or 'exit' to quit): ").strip()
        
        if subcat_choice.lower() == 'exit':
            return False
        
        try:
            subcat_idx = int(subcat_choice) - 1
            if 0 <= subcat_idx < len(subcategories):
                subcategory = subcategories[subcat_idx]
                return self._update_keywords(dict_name, subcategory)
            else:
                print(f"\nInvalid {item_name} number.")
        except ValueError:
            print(f"\nPlease enter a valid {item_name} number.")
        
        return True
    
    def _remove_subcategory(self, dict_name, subcategories):
        """Remove a subcategory."""
        item_name = dict_name[:-1]
        try:
            subcat_choice = input(f"\nSelect {item_name} to remove (number) or Enter to cancel: ").strip()
            if not subcat_choice:
                return
            
            subcat_idx = int(subcat_choice) - 1
            if 0 <= subcat_idx < len(subcategories):
                subcategory = subcategories[subcat_idx]
                if self._confirm_action(f"remove {item_name} '{subcategory}'"):
                    if self.updater.remove_subcategory(dict_name, subcategory):
                        print(f"\n{item_name.capitalize()} '{subcategory}' removed successfully.")
                        self._save_changes()
        except ValueError:
            print(f"\nPlease enter a valid {item_name} number.")
    
    def _update_subcategories(self, dict_name, persona=None):
        """Update subcategories for a dictionary."""
        while True:
            subcategories = self.updater.get_subcategories(dict_name, persona)
            choice = self._get_subcategories_menu_choice(dict_name, persona, subcategories)
            
            if choice == "1":
                self._add_subcategory_with_persona(dict_name, persona)
            elif choice == "2":
                if subcategories and not self._update_subcategory_with_persona(dict_name, subcategories, persona):
                    return False
            elif choice == "3":
                if subcategories:
                    self._remove_subcategory_with_persona(dict_name, subcategories, persona)
            elif choice == "4":
                return True
            elif choice == "5":
                return False
            else:
                print("\nInvalid choice. Please try again.")
    
    def _get_subcategories_menu_choice(self, dict_name, persona, subcategories):
        """Display subcategories menu."""
        print(f"\n{'=' * 50}")
        if persona:
            print(f"UPDATE {dict_name.upper()} FOR PERSONA '{persona.upper()}'")
        else:
            print(f"UPDATE {dict_name.upper()}")
        
        if subcategories:
            print("\nAvailable subcategories:")
            for i, subcat in enumerate(subcategories, 1):
                print(f"{i}. {subcat}")
        
        print("\nOPTIONS:")
        print("1. Add new subcategory")
        print("2. Update existing subcategory")
        print("3. Remove a subcategory")
        print("4. Back to previous menu")
        print("5. Exit")
        
        return input("\nEnter your choice [1-5]: ").strip()
    
    def _add_subcategory_with_persona(self, dict_name, persona):
        """Add subcategory with persona support."""
        subcategory = input("\nEnter new subcategory name (or 'exit' to quit): ").strip().lower()
        
        if subcategory == 'exit':
            return False
        
        if not subcategory:
            print("\nSubcategory name cannot be empty.")
            return True
        
        if self.updater.add_subcategory(dict_name, subcategory, persona):
            print(f"\nSubcategory '{subcategory}' added successfully.")
            self._add_initial_keywords_with_persona(dict_name, subcategory, persona)
            self._save_changes()
        else:
            print(f"\nFailed to add subcategory '{subcategory}'.")
        
        return True
    
    def _add_initial_keywords_with_persona(self, dict_name, subcategory, persona):
        """Add initial keywords with persona support."""
        keywords = input("\nEnter initial keywords (comma-separated) or press Enter to skip: ").strip()
        if keywords:
            for keyword in keywords.split(','):
                keyword = keyword.strip().lower()
                if keyword:
                    self.updater.add_keyword(dict_name, subcategory, keyword, persona)
    
    def _update_subcategory_with_persona(self, dict_name, subcategories, persona):
        """Update subcategory with persona support."""
        subcat_choice = input("\nEnter subcategory number to update (or 'exit' to quit): ").strip()
        
        if subcat_choice.lower() == 'exit':
            return False
        
        try:
            subcat_idx = int(subcat_choice) - 1
            if 0 <= subcat_idx < len(subcategories):
                subcategory = subcategories[subcat_idx]
                return self._update_keywords(dict_name, subcategory, persona)
            else:
                print("\nInvalid subcategory number.")
        except ValueError:
            print("\nPlease enter a valid subcategory number.")
        
        return True
    
    def _remove_subcategory_with_persona(self, dict_name, subcategories, persona):
        """Remove subcategory with persona support."""
        try:
            subcat_choice = input("\nSelect subcategory to remove (number) or Enter to cancel: ").strip()
            if not subcat_choice:
                return
            
            subcat_idx = int(subcat_choice) - 1
            if 0 <= subcat_idx < len(subcategories):
                subcategory = subcategories[subcat_idx]
                if self._confirm_action(f"remove subcategory '{subcategory}'"):
                    if self.updater.remove_subcategory(dict_name, subcategory, persona):
                        print(f"\nSubcategory '{subcategory}' removed successfully.")
                        self._save_changes()
        except ValueError:
            print("\nPlease enter a valid subcategory number.")
    
    def _update_keywords(self, dict_name, subcategory, persona=None):
        """Update keywords for a subcategory."""
        while True:
            try:
                keywords = self.updater.get_keywords(dict_name, subcategory, persona)
                choice = self._get_keywords_menu_choice(subcategory, keywords)
                
                if choice == "1":
                    self._add_keyword(dict_name, subcategory, keywords, persona)
                elif choice == "2":
                    if keywords:
                        self._remove_keyword(dict_name, subcategory, keywords, persona)
                elif choice == "3":
                    return True
                elif choice == "4":
                    return False
                else:
                    print("\nInvalid choice. Please try again.")
                    
            except ValueError as e:
                print(f"\nError: {e}")
                return True
    
    def _get_keywords_menu_choice(self, subcategory, keywords):
        """Display keywords menu."""
        print(f"\n{'=' * 50}")
        print(f"KEYWORDS FOR {subcategory.upper()}:")
        
        if keywords:
            for i, keyword in enumerate(keywords, 1):
                print(f"{i}. {keyword}")
        else:
            print("No keywords found.")
        
        print("\nOPTIONS:")
        print("1. Add a keyword")
        print("2. Remove a keyword") 
        print("3. Back to previous menu")
        print("4. Exit")
        
        return input("\nEnter your choice [1-4]: ").strip()
    
    def _add_keyword(self, dict_name, subcategory, existing_keywords, persona):
        """Add a keyword."""
        keyword = input("\nEnter new keyword (or 'exit' to quit): ").strip().lower()
        
        if keyword == 'exit':
            return False
        
        if not keyword:
            print("\nKeyword cannot be empty.")
            return True
        
        if keyword in existing_keywords:
            print(f"\nKeyword '{keyword}' already exists.")
            return True
        
        if self.updater.add_keyword(dict_name, subcategory, keyword, persona):
            print(f"\nKeyword '{keyword}' added successfully.")
            self._save_changes()
        else:
            print(f"\nFailed to add keyword '{keyword}'.")
        
        return True
    
    def _remove_keyword(self, dict_name, subcategory, keywords, persona):
        """Remove a keyword."""
        try:
            keyword_choice = input("\nSelect keyword to remove (number) or Enter to cancel: ").strip()
            if not keyword_choice:
                return
            
            keyword_idx = int(keyword_choice) - 1
            if 0 <= keyword_idx < len(keywords):
                keyword = keywords[keyword_idx]
                if self._confirm_action(f"remove keyword '{keyword}'"):
                    if self.updater.remove_keyword(dict_name, subcategory, keyword, persona):
                        print(f"\nKeyword '{keyword}' removed successfully.")
                        self._save_changes()
        except ValueError:
            print("\nPlease enter a valid keyword number.")
    
    def _confirm_action(self, action):
        """Get user confirmation for an action."""
        return input(f"\nAre you sure you want to {action}? (y/n): ").strip().lower() == 'y'
    
    def _save_changes(self):
        """Save changes to dictionary."""
        self.updater.save_changes()
        print("Changes saved successfully.")
        
    def _update_blacklist(self):
        """Handle blacklist updates."""
        while True:
            blacklisted_apps = self.updater.get_blacklisted_apps()
            choice = self._get_blacklist_menu_choice(blacklisted_apps)
            
            if choice == "1":
                self._add_blacklisted_app()
            elif choice == "2":
                if blacklisted_apps:
                    self._remove_blacklisted_app(blacklisted_apps)
            elif choice == "3":
                return True
            elif choice == "4":
                return False
            else:
                print("\nInvalid choice. Please try again.")

    def _get_blacklist_menu_choice(self, blacklisted_apps):
        """Display blacklist menu."""
        print("\n" + "=" * 50)
        print("UPDATE BLACKLISTED APPS")
        
        if blacklisted_apps:
            print("\nCurrently blacklisted apps:")
            for i, app in enumerate(blacklisted_apps, 1):
                print(f"{i}. {app}")
        else:
            print("\nNo apps currently blacklisted.")
        
        print("\nOPTIONS:")
        print("1. Add app to blacklist")
        print("2. Remove app from blacklist")
        print("3. Back to main menu")
        print("4. Exit")
        
        return input("\nEnter your choice [1-4]: ").strip()

    def _add_blacklisted_app(self):
        """Add an app to blacklist."""
        app_identifier = input("\nEnter app name or package name to blacklist (or 'exit' to quit): ").strip()
        
        if app_identifier.lower() == 'exit':
            return False
        
        if not app_identifier:
            print("\nApp identifier cannot be empty.")
            return True
        
        if self.updater.add_blacklisted_app(app_identifier):
            print(f"\nApp '{app_identifier}' added to blacklist successfully.")
            self._save_changes()
        else:
            print(f"\nFailed to add app '{app_identifier}' to blacklist.")
        
        return True

    def _remove_blacklisted_app(self, blacklisted_apps):
        """Remove an app from blacklist."""
        try:
            app_choice = input("\nSelect app to remove from blacklist (number) or Enter to cancel: ").strip()
            if not app_choice:
                return
            
            app_idx = int(app_choice) - 1
            if 0 <= app_idx < len(blacklisted_apps):
                app = blacklisted_apps[app_idx]
                if self._confirm_action(f"remove '{app}' from blacklist"):
                    if self.updater.remove_blacklisted_app(app):
                        print(f"\nApp '{app}' removed from blacklist successfully.")
                        self._save_changes()
            else:
                print("\nInvalid app number.")
        except ValueError:
            print("\nPlease enter a valid app number.")
            

# Convenience function for backward compatibility
def update_dictionaries_interactively():
    """Interactive function to update categorization dictionaries."""
    manager = DictionaryManager()
    manager.run_interactive_updater()

class BlacklistError(Exception):
    """Exception raised when processing blacklisted apps."""
    def __init__(self, app_name):
        self.app_name = app_name
        super().__init__(f"App '{app_name}' is blacklisted and cannot be processed")