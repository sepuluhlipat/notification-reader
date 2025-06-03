import numpy as np
import pandas as pd
from datetime import datetime
import re
from enum import Enum
import io
import dictionary.dictionary as dictionary
from dictionary_updater import DictionaryUpdater
from persona_manager import PersonaManager, run_persona_selector


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
    def __init__(self):
        """Initialize parser with unified dictionaries."""
        self._load_dictionaries()
        self._compile_patterns()
    
    def _load_dictionaries(self):
        """Load all required dictionaries."""
        # Load from unified dictionary structure
        self.categories = dictionary.get_categories()
        self.merchants = dictionary.get_merchants()
        self.transaction_types = dictionary.get_transaction_types()
        self.blacklisted_apps = dictionary.get_blacklist()
    
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
    
    def reload_dictionaries(self):
        """Reload dictionaries (useful after updates)."""
        self._load_dictionaries()
    
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
        app_lower = app_identifier.lower().strip()

        for blacklisted_app in self.blacklisted_apps:
            if blacklisted_app.lower() in app_lower or app_lower in blacklisted_app.lower():
                return True
        return False


def process_notification_data(df):
    """Process notifications dataframe to extract structured transaction data."""
    parser = NotificationParser()
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


def test_raw_csv_input(raw_input):
    """Test notifications using raw CSV input without headers."""
    try:
        column_names = ['ID', 'PACKAGE NAME', 'APP LABEL', 'MESSAGE', 'DATE', 'CONTENTS', 'TIMESTAMP']
        
        if '\n' not in raw_input:
            raw_input += '\n'
            
        df = pd.read_csv(io.StringIO(raw_input), names=column_names, header=None)
        result_df = process_notification_data(df)
        
        return [row.to_dict() for _, row in result_df.iterrows()]
        
    except Exception as e:
        return [{"error": f"Failed to parse CSV: {str(e)}"}]


class DictionaryManager:
    """Manages dictionary updates with a cleaner interface."""
    
    def __init__(self):
        self.updater = DictionaryUpdater(dictionary)
        self.persona_manager = PersonaManager(dictionary)
    
    def run_interactive_updater(self):
        """Main interactive dictionary updater."""
        print("\n" + "=" * 50)
        print("DICTIONARY UPDATER")
        print("Update transaction categorization dictionaries or apply personas")
        print(f"Available features: Dictionary Updates, Persona Selection")
        
        # Show current statistics
        stats = self.updater.get_dictionary_stats()
        print(f"\nCurrent Statistics:")
        for dict_name, stat in stats.items():
            if dict_name == 'blacklist':
                print(f"  {dict_name}: {stat['total_apps']} apps")
            else:
                if isinstance(stat, dict) and 'subcategories' in stat:
                    print(f"  {dict_name}: {stat['subcategories']} subcategories, {stat['total_keywords']} keywords")
                else:
                    # Handle simple dictionary structure
                    total_items = len(stat) if isinstance(stat, (list, dict)) else 0
                    print(f"  {dict_name}: {total_items} items")
                    
        while True:
            choice = self._get_main_menu_choice()
            
            if choice == "1":
                # Persona selector
                self.persona_manager.run_persona_selector()
                # Reload updater after potential persona change
                self.updater = DictionaryUpdater(dictionary)
            elif choice == "2":
                if not self._update_dictionary("categories"):
                    break
            elif choice == "3":
                if not self._update_dictionary("merchants"):
                    break
            elif choice == "4":
                if not self._update_dictionary("transaction_types"):
                    break
            elif choice == "5":
                if not self._update_blacklist():
                    break
            elif choice == "6":
                self._show_dictionary_stats()
            elif choice == "7":
                print("\nExiting dictionary manager.")
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def _get_main_menu_choice(self):
        """Display main menu and get user choice."""
        print("\n" + "=" * 50)
        print("DICTIONARY MANAGER MENU")
        print("1. Select & Apply Persona (Replace Categories)")
        print("2. Update Categories")
        print("3. Update Merchants") 
        print("4. Update Transaction Types")
        print("5. Update Blacklisted Apps")
        print("6. Show Statistics")
        print("7. Exit")
        return input(f"\nEnter your choice [1-7]: ").strip()
    
    def _show_dictionary_stats(self):
        """Display detailed dictionary statistics."""
        stats = self.updater.get_dictionary_stats()
        print(f"\n{'=' * 50}")
        print("DICTIONARY STATISTICS")
        print(f"{'=' * 50}")
        
        for dict_name, stat in stats.items():
            print(f"\n{dict_name.upper()}:")
            if dict_name == 'blacklist':
                print(f"  Total blacklisted apps: {stat['total_apps']}")
                if stat['total_apps'] > 0:
                    apps = self.updater.get_blacklisted_apps()
                    print(f"  Apps: {', '.join(apps[:5])}")
                    if len(apps) > 5:
                        print(f"        ... and {len(apps) - 5} more")
            else:
                print(f"  Subcategories: {stat['subcategories']}")
                print(f"  Total keywords: {stat['total_keywords']}")
                
                # Show subcategories with keyword counts
                subcategories = self.updater.get_subcategories(dict_name)
                if subcategories:
                    print("  Breakdown:")
                    for subcat in subcategories[:5]:  # Show first 5
                        try:
                            keywords = self.updater.get_keywords(dict_name, subcat)
                            print(f"    {subcat}: {len(keywords)} keywords")
                        except:
                            print(f"    {subcat}: 0 keywords")
                    if len(subcategories) > 5:
                        print(f"    ... and {len(subcategories) - 5} more subcategories")
        
        input("\nPress Enter to continue...")
    
    def _update_dictionary(self, dict_name):
        """Update categories, merchants, or transaction_types dictionary."""
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
                if subcategories:
                    self._view_subcategory_details(dict_name, subcategories)
            elif choice == "5":
                return True
            elif choice == "6":
                return False
            else:
                print("\nInvalid choice. Please try again.")
    
    def _get_dictionary_menu_choice(self, dict_name, subcategories):
        """Display dictionary update menu."""
        print(f"\n{'=' * 50}")
        print(f"UPDATE {dict_name.upper()}")
        
        if subcategories:
            print(f"\nAvailable {dict_name} ({len(subcategories)} total):")
            for i, subcat in enumerate(subcategories[:10], 1):  # Show first 10
                try:
                    keywords = self.updater.get_keywords(dict_name, subcat)
                    print(f"{i}. {subcat} ({len(keywords)} keywords)")
                except:
                    print(f"{i}. {subcat} (0 keywords)")
            if len(subcategories) > 10:
                print(f"... and {len(subcategories) - 10} more")
        else:
            print(f"\nNo {dict_name} found.")
        
        item_name = dict_name[:-1] if dict_name.endswith('s') else dict_name
        print(f"\nOPTIONS:")
        print(f"1. Add new {item_name}")
        print(f"2. Update existing {item_name}")
        print(f"3. Remove a {item_name}")
        print(f"4. View details")
        print("5. Back to main menu")
        print("6. Exit")
        
        return input("\nEnter your choice [1-6]: ").strip()
    
    def _view_subcategory_details(self, dict_name, subcategories):
        """View detailed information about subcategories."""
        print(f"\n{'=' * 50}")
        print(f"{dict_name.upper()} DETAILS")
        print(f"{'=' * 50}")
        
        for i, subcat in enumerate(subcategories, 1):
            try:
                keywords = self.updater.get_keywords(dict_name, subcat)
                print(f"\n{i}. {subcat} ({len(keywords)} keywords):")
                if keywords:
                    # Show first 10 keywords
                    for j, keyword in enumerate(keywords[:10]):
                        print(f"    - {keyword}")
                    if len(keywords) > 10:
                        print(f"    ... and {len(keywords) - 10} more keywords")
                else:
                    print("    (no keywords)")
            except Exception as e:
                print(f"\n{i}. {subcat}: Error loading keywords - {e}")
        
        input("\nPress Enter to continue...")
    
    def _add_subcategory(self, dict_name):
        """Add a subcategory to dictionary."""
        item_name = dict_name[:-1] if dict_name.endswith('s') else dict_name
        subcat_name = input(f"\nEnter new {item_name} name (or 'exit' to quit): ").strip()
        
        if subcat_name.lower() == 'exit':
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
            added_count = 0
            for keyword in keywords.split(','):
                keyword = keyword.strip()
                if keyword:
                    if self.updater.add_keyword(dict_name, subcat_name, keyword, check_conflicts=False):
                        added_count += 1
            print(f"Added {added_count} keywords to '{subcat_name}'.")
    
    def _update_subcategory(self, dict_name, subcategories):
        """Update a subcategory."""
        item_name = dict_name[:-1] if dict_name.endswith('s') else dict_name
        
        print(f"\nAvailable {item_name}s:")
        for i, subcat in enumerate(subcategories, 1):
            try:
                keywords = self.updater.get_keywords(dict_name, subcat)
                print(f"{i}. {subcat} ({len(keywords)} keywords)")
            except:
                print(f"{i}. {subcat} (0 keywords)")
        
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
        item_name = dict_name[:-1] if dict_name.endswith('s') else dict_name
        
        print(f"\nAvailable {item_name}s:")
        for i, subcat in enumerate(subcategories, 1):
            try:
                keywords = self.updater.get_keywords(dict_name, subcat)
                print(f"{i}. {subcat} ({len(keywords)} keywords)")
            except:
                print(f"{i}. {subcat} (0 keywords)")
        
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
                    else:
                        print(f"\nFailed to remove {item_name} '{subcategory}'.")
            else:
                print(f"\nInvalid {item_name} number.")
        except ValueError:
            print(f"\nPlease enter a valid {item_name} number.")
    
    def _update_keywords(self, dict_name, subcategory):
        """Update keywords for a subcategory."""
        while True:
            try:
                keywords = self.updater.get_keywords(dict_name, subcategory)
                choice = self._get_keywords_menu_choice(subcategory, keywords)
                
                if choice == "1":
                    self._add_keyword(dict_name, subcategory, keywords)
                elif choice == "2":
                    if keywords:
                        self._remove_keyword(dict_name, subcategory, keywords)
                elif choice == "3":
                    if keywords:
                        self._bulk_add_keywords(dict_name, subcategory)
                elif choice == "4":
                    return True
                elif choice == "5":
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
            print(f"\nCurrent keywords ({len(keywords)} total):")
            for i, keyword in enumerate(keywords[:15], 1):  # Show first 15
                print(f"{i}. {keyword}")
            if len(keywords) > 15:
                print(f"... and {len(keywords) - 15} more keywords")
        else:
            print("\nNo keywords found.")
        
        print("\nOPTIONS:")
        print("1. Add a keyword")
        print("2. Remove a keyword")
        print("3. Bulk add keywords")
        print("4. Back to previous menu")
        print("5. Exit")
        
        return input("\nEnter your choice [1-5]: ").strip()
    
    def _add_keyword(self, dict_name, subcategory, existing_keywords):
        """Add a keyword."""
        keyword = input("\nEnter new keyword (or 'exit' to quit): ").strip()
        
        if keyword.lower() == 'exit':
            return False
        
        if not keyword:
            print("\nKeyword cannot be empty.")
            return True
        
        if self.updater.add_keyword(dict_name, subcategory, keyword):
            print(f"\nKeyword '{keyword}' added successfully.")
            self._save_changes()
        else:
            print(f"\nFailed to add keyword '{keyword}'.")
        
        return True
    
    def _bulk_add_keywords(self, dict_name, subcategory):
        """Add multiple keywords at once."""
        print(f"\nBulk add keywords to '{subcategory}'")
        keywords = input("Enter keywords separated by commas: ").strip()
        
        if not keywords:
            print("No keywords entered.")
            return
        
        added_count = 0
        skipped_count = 0
        
        for keyword in keywords.split(','):
            keyword = keyword.strip()
            if keyword:
                if self.updater.add_keyword(dict_name, subcategory, keyword, check_conflicts=False):
                    added_count += 1
                else:
                    skipped_count += 1
        
        print(f"\nAdded {added_count} keywords, skipped {skipped_count} (duplicates or errors).")
        if added_count > 0:
            self._save_changes()
    
    def _remove_keyword(self, dict_name, subcategory, keywords):
        """Remove a keyword."""
        print(f"\nKeywords in '{subcategory}':")
        for i, keyword in enumerate(keywords, 1):
            print(f"{i}. {keyword}")
        
        try:
            keyword_choice = input("\nSelect keyword to remove (number) or Enter to cancel: ").strip()
            if not keyword_choice:
                return
            
            keyword_idx = int(keyword_choice) - 1
            if 0 <= keyword_idx < len(keywords):
                keyword = keywords[keyword_idx]
                if self._confirm_action(f"remove keyword '{keyword}'"):
                    if self.updater.remove_keyword(dict_name, subcategory, keyword):
                        print(f"\nKeyword '{keyword}' removed successfully.")
                        self._save_changes()
                    else:
                        print(f"\nFailed to remove keyword '{keyword}'.")
            else:
                print("\nInvalid keyword number.")
        except ValueError:
            print("\nPlease enter a valid keyword number.")
    
    def _confirm_action(self, action):
        """Get user confirmation for an action."""
        return input(f"\nAre you sure you want to {action}? (y/n): ").strip().lower() == 'y'
    
    def _save_changes(self):
        """Save changes to dictionary."""
        if self.updater.save_changes():
            print("Changes saved successfully.")
        else:
            print("Failed to save changes.")
        
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