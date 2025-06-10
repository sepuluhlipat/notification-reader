"""
Dictionary management interface for interactive dictionary updates.

This module provides the DictionaryManager class which offers a clean
interactive interface for managing transaction categorization dictionaries.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dictionary.dictionary as dictionary
from ..dictionary import dictionary
from .updater import DictionaryUpdater
from .persona import PersonaManager


class DictionaryManager:
    """Manages dictionary updates with a cleaner interface."""
    
    def __init__(self):
        self.updater = DictionaryUpdater(dictionary)
        self.persona_manager = PersonaManager(dictionary)
    
    def run_interactive_updater(self):
        """Main interactive dictionary updater."""
        print("\n" + "=" * 50)
        print("DICTIONARY MANAGER")
        print("Update transaction categorization dictionaries or apply personas")
        
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
    
    def _confirm_action(self, action):
        """Get user confirmation for an action."""
        return input(f"\nAre you sure you want to {action}? (y/n): ").strip().lower() == 'y'
    
    def _save_changes(self):
        """Save changes to dictionary."""
        if self.updater.save_changes():
            print("Changes saved successfully.")
        else:
            print("Failed to save changes.")