"""
Enhanced Dictionary updater module for the transaction categorization system.
Allows users to view and edit dictionary entries and save changes to a single JSON file.
Uses a unified dictionary structure with categories, merchants, transaction_types, and blacklist.
Removes persona-based categorization - uses only general categories.
"""
import json
import os
from typing import Dict, List, Any, Tuple, Optional


class DictionaryUpdater:
    def __init__(self, dictionary_module=None):
        """Initialize the dictionary updater with path to the unified JSON file."""
        self.dictionary_module = dictionary_module
        
        # Define path to the unified JSON file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self._file_path = os.path.join(current_dir, 'dictionary.json')
        
        self._load_dictionaries()
    
    def _load_dictionaries(self) -> None:
        """Load all dictionaries from the unified JSON file or dictionary module."""
        if self.dictionary_module:
            self.dictionaries = self.dictionary_module.get_all_dictionaries()
        else:
            self.dictionaries = self._load_json_file(self._file_path)
        
        # Ensure all required sections exist
        if 'categories' not in self.dictionaries:
            self.dictionaries['categories'] = {}
        if 'merchants' not in self.dictionaries:
            self.dictionaries['merchants'] = {}
        if 'transaction_types' not in self.dictionaries:
            self.dictionaries['transaction_types'] = {}
        if 'blacklist' not in self.dictionaries:
            self.dictionaries['blacklist'] = []
    
    def _load_json_file(self, file_path: str) -> Dict:
        """Load data from the unified JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading JSON file {file_path}: {e}")
            return {
                'categories': {},
                'merchants': {},
                'transaction_types': {},
                'blacklist': []
            }
    
    def _save_json_file(self, file_path: str, data: Dict) -> bool:
        """Save data to the unified JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2)
            return True
        except Exception as e:
            print(f"Error saving JSON file {file_path}: {e}")
            return False
    
    def get_dictionary_section(self, dictionary_name: str) -> Dict:
        """Get a specific dictionary section by name."""
        if dictionary_name not in ['categories', 'merchants', 'transaction_types']:
            raise ValueError(f"Unknown dictionary: {dictionary_name}")
        
        return self.dictionaries.get(dictionary_name, {})
    
    def _find_matching_keyword(self, keywords: List[str], target_keyword: str) -> Optional[str]:
        """Find a keyword that matches the target (case-insensitive)."""
        target_lower = target_keyword.lower()
        for keyword in keywords:
            if keyword.lower() == target_lower:
                return keyword
        return None
    
    def find_keyword_conflicts(self, dictionary_name: str, keyword: str, 
                             exclude_subcategory: str = None) -> List[Dict[str, str]]:
        """Find all occurrences of a keyword within the specified dictionary."""
        conflicts = []
        keyword_lower = keyword.strip().lower()
        dictionary = self.get_dictionary_section(dictionary_name)
        
        for subcategory, keywords in dictionary.items():
            if exclude_subcategory and subcategory == exclude_subcategory:
                continue
            
            matching_keyword = self._find_matching_keyword(keywords, keyword_lower)
            if matching_keyword:
                conflicts.append({
                    'dictionary': dictionary_name,
                    'subcategory': subcategory,
                    'conflicting_keyword': matching_keyword,
                    'location': f"{dictionary_name} -> {subcategory}"
                })
        
        return conflicts
    
    def find_subcategory_conflicts(self, dictionary_name: str, subcategory: str) -> List[Dict[str, Any]]:
        """Find if a subcategory name exists in the specified dictionary."""
        conflicts = []
        subcategory_lower = subcategory.strip().lower()
        dictionary = self.get_dictionary_section(dictionary_name)
        
        for existing_subcategory, keywords in dictionary.items():
            if existing_subcategory.lower() == subcategory_lower:
                conflicts.append({
                    'dictionary': dictionary_name,
                    'subcategory': existing_subcategory,
                    'keywords': keywords,
                    'keywords_count': len(keywords),
                    'location': f"{dictionary_name} -> {existing_subcategory}"
                })
        
        return conflicts
    
    def find_cross_dictionary_conflicts(self, keyword: str, exclude_dictionary: str = None) -> List[Dict[str, str]]:
        """Find conflicts across all dictionaries for a given keyword."""
        all_conflicts = []
        keyword_lower = keyword.strip().lower()
        
        for dict_name in ["categories", "merchants", "transaction_types"]:
            if exclude_dictionary and dict_name == exclude_dictionary:
                continue
            
            dictionary = self.get_dictionary_section(dict_name)
            
            for subcategory, keywords in dictionary.items():
                matching_keyword = self._find_matching_keyword(keywords, keyword_lower)
                if matching_keyword:
                    all_conflicts.append({
                        'dictionary': dict_name,
                        'subcategory': subcategory,
                        'conflicting_keyword': matching_keyword,
                        'location': f"{dict_name} -> {subcategory}"
                    })
        
        return all_conflicts
    
    def get_conflict_summary(self, conflicts: List[Dict[str, Any]]) -> str:
        """Generate a human-readable summary of conflicts."""
        if not conflicts:
            return "No conflicts found."
        
        summary = f"Found {len(conflicts)} conflict(s):\n"
        for i, conflict in enumerate(conflicts, 1):
            location = conflict['location']
            
            if 'conflicting_keyword' in conflict:
                # Keyword conflict
                conflicting_keyword = conflict['conflicting_keyword']
                summary += f"  {i}. {location} (keyword: '{conflicting_keyword}')\n"
            elif 'keywords' in conflict:
                # Subcategory conflict
                keywords = conflict['keywords']
                keywords_count = conflict['keywords_count']
                
                if keywords_count == 0:
                    summary += f"  {i}. {location} (empty subcategory)\n"
                elif keywords_count <= 5:
                    keywords_str = ", ".join(keywords)
                    summary += f"  {i}. {location} (keywords: {keywords_str})\n"
                else:
                    keywords_str = ", ".join(keywords[:5])
                    remaining = keywords_count - 5
                    summary += f"  {i}. {location} (keywords: {keywords_str} ... and {remaining} more)\n"
            else:
                summary += f"  {i}. {location}\n"
        
        return summary
    
    def prompt_user_for_conflict_resolution(self, keyword: str, conflicts: List[Dict[str, str]], 
                                          action_type: str = "add") -> bool:
        """Prompt user to resolve conflicts and decide whether to proceed."""
        if not conflicts:
            return True
        
        print(f"\n{'='*60}")
        print(f"CONFLICT DETECTED FOR KEYWORD: '{keyword}'")
        print(f"{'='*60}")
        print(f"This keyword already exists in the following location(s):")
        print(self.get_conflict_summary(conflicts))
        
        options = [
            f"1. Proceed with {action_type} (creates duplicate)",
            f"2. Cancel {action_type}"
        ]
        if action_type == "add":
            options.append("3. Remove from existing location(s) and add to new location")
        options.append("4. View details of existing entries")
        
        print(f"\nWhat would you like to do?")
        for option in options:
            print(option)
        
        while True:
            choice = input(f"\nEnter your choice [1-4]: ").strip()
            
            if choice == "1":
                confirm = input(f"\nAre you sure you want to create a duplicate entry? (y/n): ").strip().lower()
                return confirm == 'y'
            elif choice == "2":
                print(f"\n{action_type.capitalize()} cancelled.")
                return False
            elif choice == "3" and action_type == "add":
                return self._handle_keyword_migration(keyword, conflicts)
            elif choice == "4":
                self._show_conflict_details(keyword, conflicts)
                continue
            else:
                print("Invalid choice. Please try again.")
    
    def _handle_keyword_migration(self, keyword: str, conflicts: List[Dict[str, str]]) -> bool:
        """Handle migration of keyword from existing locations to new location."""
        print(f"\nThis will remove '{keyword}' from the following location(s):")
        print(self.get_conflict_summary(conflicts))
        
        confirm = input(f"\nProceed with removal from existing location(s)? (y/n): ").strip().lower()
        if confirm != 'y':
            return False
        
        # Remove from existing locations
        for conflict in conflicts:
            try:
                keyword_to_remove = conflict.get('conflicting_keyword', keyword)
                success = self.remove_keyword(conflict['dictionary'], conflict['subcategory'], keyword_to_remove)
                location = f"{conflict['dictionary']} -> {conflict['subcategory']}"
                
                if success:
                    print(f"Removed '{keyword_to_remove}' from {location}")
                else:
                    print(f"Failed to remove '{keyword_to_remove}' from {location}")
                    
            except Exception as e:
                print(f"Error removing keyword from {conflict['location']}: {e}")
        
        return True
    
    def _show_conflict_details(self, keyword: str, conflicts: List[Dict[str, str]]) -> None:
        """Show detailed information about conflicts."""
        print(f"\n{'='*60}")
        print(f"DETAILED CONFLICT INFORMATION FOR: '{keyword}'")
        print(f"{'='*60}")
        
        for i, conflict in enumerate(conflicts, 1):
            print(f"\nConflict {i}:")
            print(f"  Location: {conflict['location']}")
            
            if 'conflicting_keyword' in conflict:
                print(f"  Conflicting keyword: '{conflict['conflicting_keyword']}'")
            
            # Show other keywords in the same subcategory
            try:
                keywords = self.get_keywords(conflict['dictionary'], conflict['subcategory'])
                other_keywords = [k for k in keywords if k.lower() != keyword.lower()]
                if other_keywords:
                    print(f"  Other keywords in same subcategory: {', '.join(other_keywords[:5])}")
                    if len(other_keywords) > 5:
                        print(f"    ... and {len(other_keywords) - 5} more")
                else:
                    print(f"  No other keywords in this subcategory")
                    
            except Exception as e:
                print(f"  Error retrieving keywords: {e}")
    
    def save_changes(self) -> bool:
        """Save all dictionaries to the unified JSON file."""
        result = self._save_json_file(self._file_path, self.dictionaries)
        
        if result and self.dictionary_module:
            self.dictionary_module.reload_dictionaries()
            
        return result
    
    def get_available_dictionaries(self) -> List[str]:
        """Get a list of available dictionaries that can be updated."""
        return ['categories', 'merchants', 'transaction_types', 'blacklist']
    
    def get_subcategories(self, dictionary_name: str) -> List[str]:
        """Get available subcategories for a given dictionary."""
        if dictionary_name == 'blacklist':
            return []  # Blacklist doesn't have subcategories
        
        dictionary = self.get_dictionary_section(dictionary_name)
        return list(dictionary.keys())
    
    def get_keywords(self, dictionary_name: str, subcategory: str) -> List[str]:
        """Get keywords for a specific subcategory."""
        if dictionary_name == 'blacklist':
            raise ValueError("Blacklist doesn't have subcategories or keywords")
        
        dictionary = self.get_dictionary_section(dictionary_name)
        
        if subcategory in dictionary:
            return dictionary[subcategory]
        else:
            raise ValueError(f"Subcategory '{subcategory}' not found in {dictionary_name} dictionary")
    
    def _keyword_exists_in_subcategory(self, dictionary_name: str, subcategory: str, keyword: str) -> bool:
        """Check if a keyword already exists in a subcategory."""
        try:
            existing_keywords = self.get_keywords(dictionary_name, subcategory)
            return any(k.lower() == keyword.lower() for k in existing_keywords)
        except:
            return False
    
    def add_keyword(self, dictionary_name: str, subcategory: str, keyword: str, 
                   check_conflicts: bool = True) -> bool:
        """Add a keyword to a subcategory with improved conflict checking."""
        if dictionary_name == 'blacklist':
            raise ValueError("Use add_blacklisted_app() for blacklist management")
        
        keyword = keyword.strip().lower()
        if not keyword:
            return False
        
        # Check if keyword already exists in the target subcategory
        if self._keyword_exists_in_subcategory(dictionary_name, subcategory, keyword):
            print(f"Keyword '{keyword}' already exists in {dictionary_name} -> {subcategory}.")
            return False
        
        # Check for conflicts if requested
        if check_conflicts:
            # Check for conflicts within the same dictionary
            conflicts = self.find_keyword_conflicts(dictionary_name, keyword, subcategory)
            
            # Show cross-dictionary conflicts as warnings
            cross_conflicts = self.find_cross_dictionary_conflicts(keyword, dictionary_name)
            if cross_conflicts:
                print(f"\nWARNING: '{keyword}' also exists in other dictionaries:")
                print(self.get_conflict_summary(cross_conflicts))
                print("This may cause classification conflicts during transaction parsing.")
            
            # Handle conflicts within the same dictionary
            if conflicts:
                if not self.prompt_user_for_conflict_resolution(keyword, conflicts, "add"):
                    return False
        
        return self._add_keyword_to_dictionary(dictionary_name, subcategory, keyword)
    
    def _add_keyword_to_dictionary(self, dictionary_name: str, subcategory: str, keyword: str) -> bool:
        """Add keyword to the appropriate dictionary structure."""
        try:
            dictionary = self.get_dictionary_section(dictionary_name)
            
            if subcategory not in dictionary:
                dictionary[subcategory] = []
            
            dictionary[subcategory].append(keyword)
            return True
        except Exception as e:
            print(f"Error adding keyword: {e}")
            return False
    
    def remove_keyword(self, dictionary_name: str, subcategory: str, keyword: str) -> bool:
        """Remove a keyword from a subcategory."""
        if dictionary_name == 'blacklist':
            raise ValueError("Use remove_blacklisted_app() for blacklist management")
        
        keyword_lower = keyword.strip().lower()
        
        try:
            dictionary = self.get_dictionary_section(dictionary_name)
            
            if subcategory not in dictionary:
                return False
            
            keywords = dictionary[subcategory]
            
            # Find and remove the keyword (case-insensitive)
            for i, k in enumerate(keywords):
                if k.lower() == keyword_lower:
                    keywords.pop(i)
                    return True
            
            return False
        except Exception as e:
            print(f"Error removing keyword: {e}")
            return False
    
    def add_subcategory(self, dictionary_name: str, subcategory: str, check_conflicts: bool = True) -> bool:
        """Add a new subcategory to a dictionary with conflict checking."""
        if dictionary_name == 'blacklist':
            raise ValueError("Blacklist doesn't support subcategories")
        
        subcategory = subcategory.strip().lower()
        if not subcategory:
            return False
        
        # Check for conflicts if requested
        if check_conflicts:
            conflicts = self.find_subcategory_conflicts(dictionary_name, subcategory)
            
            if conflicts:
                print(f"\nCONFLICT: Subcategory '{subcategory}' already exists:")
                print(self.get_conflict_summary(conflicts))
                
                proceed = input(f"\nDo you want to proceed anyway? (y/n): ").strip().lower()
                if proceed != 'y':
                    return False
        
        return self._add_subcategory_to_dictionary(dictionary_name, subcategory)
    
    def _add_subcategory_to_dictionary(self, dictionary_name: str, subcategory: str) -> bool:
        """Add subcategory to the appropriate dictionary structure."""
        try:
            dictionary = self.get_dictionary_section(dictionary_name)
            
            if subcategory not in dictionary:
                dictionary[subcategory] = []
            
            return True
        except Exception as e:
            print(f"Error adding subcategory: {e}")
            return False
    
    def remove_subcategory(self, dictionary_name: str, subcategory: str) -> bool:
        """Remove a subcategory from a dictionary."""
        if dictionary_name == 'blacklist':
            raise ValueError("Blacklist doesn't support subcategories")
        
        try:
            dictionary = self.get_dictionary_section(dictionary_name)
            
            if subcategory not in dictionary:
                return False
            
            del dictionary[subcategory]
            return True
        except Exception as e:
            print(f"Error removing subcategory: {e}")
            return False
    
    def get_blacklisted_apps(self) -> List[str]:
        """Get the list of blacklisted apps."""
        blacklist = self.dictionaries.get('blacklist', [])
        if not isinstance(blacklist, list):
            self.dictionaries['blacklist'] = []
            return []
        return blacklist

    def add_blacklisted_app(self, app_identifier: str) -> bool:
        """Add an app to the blacklist."""
        app_identifier = app_identifier.strip()
        if not app_identifier:
            return False
        
        blacklist = self.get_blacklisted_apps()
        
        if any(app.lower() == app_identifier.lower() for app in blacklist):
            print(f"App '{app_identifier}' is already blacklisted.")
            return False
        
        blacklist.append(app_identifier)
        return True

    def remove_blacklisted_app(self, app_identifier: str) -> bool:
        """Remove an app from the blacklist."""
        blacklist = self.get_blacklisted_apps()
        
        # Find and remove the app (case-insensitive)
        for i, app in enumerate(blacklist):
            if app.lower() == app_identifier.lower():
                blacklist.pop(i)
                return True
        
        return False
    
    def get_all_dictionaries(self) -> Dict:
        """Get the complete unified dictionary structure."""
        return self.dictionaries
    
    def get_dictionary_stats(self) -> Dict[str, int]:
        """Get statistics about each dictionary section."""
        stats = {}
        
        for dict_name in ['categories', 'merchants', 'transaction_types']:
            dictionary = self.get_dictionary_section(dict_name)
            total_keywords = sum(len(keywords) for keywords in dictionary.values())
            stats[dict_name] = {
                'subcategories': len(dictionary),
                'total_keywords': total_keywords
            }
        
        blacklist = self.get_blacklisted_apps()
        stats['blacklist'] = {
            'total_apps': len(blacklist)
        }
        
        return stats