"""
Enhanced Dictionary updater module for the transaction categorization system.
Allows users to view and edit dictionary entries and save changes to JSON files.
Includes improved conflict checking with proper scoping for categories.
"""
import json
import os
from typing import Dict, List, Any, Tuple, Optional, Set

class DictionaryUpdater:
    def __init__(self, dictionary_module=None):
        """
        Initialize the dictionary updater with paths to the JSON files.
        
        Args:
            dictionary_module: The dictionary module to use for loading existing dictionaries
        """
        self.dictionary_module = dictionary_module
        
        # Define paths to JSON files
        self._CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        self._CATEGORIES_FILE = os.path.join(self._CURRENT_DIR, 'categories.json')
        self._MERCHANTS_FILE = os.path.join(self._CURRENT_DIR, 'merchants.json')
        self._TRANSACTION_TYPES_FILE = os.path.join(self._CURRENT_DIR, 'transaction_types.json')
        
        # Load dictionaries
        self._load_dictionaries()
    
    def _load_dictionaries(self) -> None:
        """Load all dictionaries from their respective JSON files."""
        if self.dictionary_module:
            self.categories = self.dictionary_module.get_all_categories()
            self.merchants = self.dictionary_module.get_merchants()
            self.transaction_types = self.dictionary_module.get_transaction_types()
        else:
            # Load directly from files if dictionary module is not provided
            self.categories = self._load_json_file(self._CATEGORIES_FILE)
            self.merchants = self._load_json_file(self._MERCHANTS_FILE)
            self.transaction_types = self._load_json_file(self._TRANSACTION_TYPES_FILE)
    
    def _load_json_file(self, file_path: str) -> Dict:
        """
        Helper function to load data from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary loaded from the JSON file or empty dict if loading fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading JSON file {file_path}: {e}")
            return {}
    
    def _save_json_file(self, file_path: str, data: Dict) -> bool:
        """
        Helper function to save data to a JSON file.
        
        Args:
            file_path: Path to the JSON file
            data: Dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2)
            return True
        except Exception as e:
            print(f"Error saving JSON file {file_path}: {e}")
            return False
    
    def find_keyword_conflicts(self, dictionary_name: str, keyword: str, exclude_subcategory: str = None, exclude_persona: str = None) -> List[Dict[str, str]]:
        """
        Find all occurrences of a keyword with proper scoping.
        
        For categories: Only search within the same persona (proper scoping)
        For merchants/transaction_types: Search across all subcategories (global scoping)
        
        Args:
            dictionary_name: Name of the dictionary to search in
            keyword: Keyword to search for
            exclude_subcategory: Subcategory to exclude from search (optional)
            exclude_persona: Persona to exclude from search (for categories only, optional)
            
        Returns:
            List of dictionaries containing conflict information
        """
        conflicts = []
        keyword = keyword.strip().lower()
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        if dictionary_name == "categories":
            # For categories: Only search within the same persona (improved scoping)
            if exclude_persona and exclude_persona in dictionary:
                persona_dict = dictionary[exclude_persona]
                
                for subcategory, keywords in persona_dict.items():
                    # Skip the subcategory we're trying to add to
                    if exclude_subcategory and subcategory == exclude_subcategory:
                        continue
                        
                    # Convert all keywords to lowercase for comparison
                    lowercase_keywords = [k.lower() for k in keywords]
                    if keyword in lowercase_keywords:
                        conflicts.append({
                            'dictionary': dictionary_name,
                            'persona': exclude_persona,
                            'subcategory': subcategory,
                            'location': f"{dictionary_name} -> {exclude_persona} -> {subcategory}"
                        })
        else:
            # For merchants and transaction_types: Search across all subcategories (global scoping)
            for subcategory, keywords in dictionary.items():
                if exclude_subcategory and subcategory == exclude_subcategory:
                    continue
                    
                # Convert all keywords to lowercase for comparison
                lowercase_keywords = [k.lower() for k in keywords]
                if keyword in lowercase_keywords:
                    conflicts.append({
                        'dictionary': dictionary_name,
                        'subcategory': subcategory,
                        'location': f"{dictionary_name} -> {subcategory}"
                    })
        
        return conflicts
    
    def find_subcategory_conflicts(self, dictionary_name: str, subcategory: str, persona: str = None) -> List[Dict[str, str]]:
        """
        Find if a subcategory name exists in other contexts within the same dictionary.
        
        Args:
            dictionary_name: Name of the dictionary to search in
            subcategory: Subcategory name to search for
            persona: Persona to exclude from search (for categories only, optional)
            
        Returns:
            List of dictionaries containing conflict information
        """
        conflicts = []
        subcategory = subcategory.strip().lower()
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        if dictionary_name == "categories":
            # For categories: Check if subcategory exists within the same persona
            if persona and persona in dictionary:
                # Convert subcategory names to lowercase for comparison
                lowercase_subcategories = {k.lower(): k for k in dictionary[persona].keys()}
                if subcategory in lowercase_subcategories:
                    conflicts.append({
                        'dictionary': dictionary_name,
                        'persona': persona,
                        'subcategory': subcategory,
                        'location': f"{dictionary_name} -> {persona} -> {subcategory}"
                    })
        else:
            # For merchants and transaction_types, subcategory names should be unique globally
            # Convert subcategory names to lowercase for comparison
            lowercase_subcategories = {k.lower(): k for k in dictionary.keys()}
            if subcategory in lowercase_subcategories:
                conflicts.append({
                    'dictionary': dictionary_name,
                    'subcategory': subcategory,
                    'location': f"{dictionary_name} -> {subcategory}"
                })
        
        return conflicts
    
    def find_cross_dictionary_conflicts(self, keyword: str, exclude_dictionary: str = None, current_persona: str = None) -> List[Dict[str, str]]:
        """
        Find conflicts across all dictionaries for a given keyword.
        This is used for warnings about potential classification conflicts.
        
        Args:
            keyword: Keyword to search for across all dictionaries
            exclude_dictionary: Dictionary to exclude from search
            current_persona: Current persona being worked with (for categories)
            
        Returns:
            List of dictionaries containing conflict information from all dictionaries
        """
        all_conflicts = []
        keyword = keyword.strip().lower()
        
        # Search in all dictionaries
        for dict_name in ["categories", "merchants", "transaction_types"]:
            if exclude_dictionary and dict_name == exclude_dictionary:
                continue
                
            if dict_name == "categories":
                # For categories, search across all personas for cross-dictionary warnings
                dictionary = self.categories
                for persona_name, persona_dict in dictionary.items():
                    for subcategory, keywords in persona_dict.items():
                        lowercase_keywords = [k.lower() for k in keywords]
                        if keyword in lowercase_keywords:
                            all_conflicts.append({
                                'dictionary': dict_name,
                                'persona': persona_name,
                                'subcategory': subcategory,
                                'location': f"{dict_name} -> {persona_name} -> {subcategory}"
                            })
            else:
                # For merchants and transaction_types, search globally
                dictionary, _ = self.get_dictionary_info(dict_name)
                for subcategory, keywords in dictionary.items():
                    lowercase_keywords = [k.lower() for k in keywords]
                    if keyword in lowercase_keywords:
                        all_conflicts.append({
                            'dictionary': dict_name,
                            'subcategory': subcategory,
                            'location': f"{dict_name} -> {subcategory}"
                        })
        
        return all_conflicts
    
    def get_conflict_summary(self, conflicts: List[Dict[str, str]]) -> str:
        """
        Generate a human-readable summary of conflicts.
        
        Args:
            conflicts: List of conflict dictionaries
            
        Returns:
            Formatted string summarizing the conflicts
        """
        if not conflicts:
            return "No conflicts found."
        
        summary = f"Found {len(conflicts)} conflict(s):\n"
        for i, conflict in enumerate(conflicts, 1):
            summary += f"  {i}. {conflict['location']}\n"
        
        return summary
    
    def prompt_user_for_conflict_resolution(self, keyword: str, conflicts: List[Dict[str, str]], action_type: str = "add") -> bool:
        """
        Prompt user to resolve conflicts and decide whether to proceed.
        
        Args:
            keyword: The keyword causing conflicts
            conflicts: List of conflicts found
            action_type: Type of action being performed ("add", "move", etc.)
            
        Returns:
            True if user wants to proceed, False otherwise
        """
        if not conflicts:
            return True
        
        print(f"\n{'='*60}")
        print(f"CONFLICT DETECTED FOR KEYWORD: '{keyword}'")
        print(f"{'='*60}")
        print(f"This keyword already exists in the following location(s):")
        print(self.get_conflict_summary(conflicts))
        
        print(f"\nWhat would you like to do?")
        print(f"1. Proceed with {action_type} (creates duplicate)")
        print(f"2. Cancel {action_type}")
        if action_type == "add":
            print(f"3. Remove from existing location(s) and add to new location")
        print(f"4. View details of existing entries")
        
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
        """
        Handle migration of keyword from existing locations to new location.
        
        Args:
            keyword: Keyword to migrate
            conflicts: List of existing locations
            
        Returns:
            True if migration should proceed, False otherwise
        """
        print(f"\nThis will remove '{keyword}' from the following location(s):")
        print(self.get_conflict_summary(conflicts))
        
        confirm = input(f"\nProceed with removal from existing location(s)? (y/n): ").strip().lower()
        if confirm != 'y':
            return False
        
        # Remove from existing locations
        for conflict in conflicts:
            try:
                if conflict['dictionary'] == 'categories':
                    persona = conflict['persona']
                    subcategory = conflict['subcategory']
                    self.remove_keyword('categories', subcategory, keyword, persona)
                    print(f"Removed '{keyword}' from categories -> {persona} -> {subcategory}")
                else:
                    subcategory = conflict['subcategory']
                    self.remove_keyword(conflict['dictionary'], subcategory, keyword)
                    print(f"Removed '{keyword}' from {conflict['dictionary']} -> {subcategory}")
            except Exception as e:
                print(f"Error removing keyword from {conflict['location']}: {e}")
        
        return True
    
    def _show_conflict_details(self, keyword: str, conflicts: List[Dict[str, str]]) -> None:
        """
        Show detailed information about conflicts.
        
        Args:
            keyword: Keyword with conflicts
            conflicts: List of conflicts
        """
        print(f"\n{'='*60}")
        print(f"DETAILED CONFLICT INFORMATION FOR: '{keyword}'")
        print(f"{'='*60}")
        
        for i, conflict in enumerate(conflicts, 1):
            print(f"\nConflict {i}:")
            print(f"  Location: {conflict['location']}")
            
            # Show other keywords in the same subcategory
            try:
                if conflict['dictionary'] == 'categories':
                    keywords = self.get_keywords('categories', conflict['subcategory'], conflict['persona'])
                else:
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
    
    def save_changes(self) -> Dict[str, bool]:
        """
        Save all dictionaries to their respective JSON files.
        
        Returns:
            Dictionary with status of each save operation
        """
        results = {
            "categories": self._save_json_file(self._CATEGORIES_FILE, self.categories),
            "merchants": self._save_json_file(self._MERCHANTS_FILE, self.merchants),
            "transaction_types": self._save_json_file(self._TRANSACTION_TYPES_FILE, self.transaction_types)
        }
        
        # If dictionary module is provided, reload dictionaries
        if self.dictionary_module:
            self.dictionary_module.reload_dictionaries()
            
        return results
    
    def get_available_dictionaries(self) -> List[str]:
        """
        Get a list of available dictionaries that can be updated.
        
        Returns:
            List of dictionary names
        """
        return ["categories", "merchants", "transaction_types"]
    
    def get_dictionary_info(self, dictionary_name: str) -> Tuple[Dict, str]:
        """
        Get a dictionary and its file path by name.
        
        Args:
            dictionary_name: Name of the dictionary to retrieve
            
        Returns:
            Tuple containing the dictionary and its file path
        """
        if dictionary_name == "categories":
            return self.categories, self._CATEGORIES_FILE
        elif dictionary_name == "merchants":
            return self.merchants, self._MERCHANTS_FILE
        elif dictionary_name == "transaction_types":
            return self.transaction_types, self._TRANSACTION_TYPES_FILE
        else:
            raise ValueError(f"Unknown dictionary: {dictionary_name}")
    
    def get_subcategories(self, dictionary_name: str, persona: str = None) -> List[str]:
        """
        Get available subcategories for a given dictionary.
        
        Args:
            dictionary_name: Name of the dictionary
            persona: Persona name for categories dictionary (optional)
            
        Returns:
            List of subcategories
        """
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        if dictionary_name == "categories":
            if persona and persona in dictionary:
                return list(dictionary[persona].keys())
            elif persona:
                raise ValueError(f"Persona '{persona}' not found in categories dictionary")
            else:
                # Return personas instead of subcategories
                return list(dictionary.keys())
        else:
            return list(dictionary.keys())
    
    def get_keywords(self, dictionary_name: str, subcategory: str, persona: str = None) -> List[str]:
        """
        Get keywords for a specific subcategory.
        
        Args:
            dictionary_name: Name of the dictionary
            subcategory: Name of the subcategory
            persona: Persona name for categories dictionary (optional)
            
        Returns:
            List of keywords
        """
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        if dictionary_name == "categories":
            if not persona:
                raise ValueError("Persona must be provided for categories dictionary")
            
            if persona in dictionary and subcategory in dictionary[persona]:
                return dictionary[persona][subcategory]
            else:
                raise ValueError(f"Subcategory '{subcategory}' not found for persona '{persona}'")
        else:
            if subcategory in dictionary:
                return dictionary[subcategory]
            else:
                raise ValueError(f"Subcategory '{subcategory}' not found in {dictionary_name} dictionary")
    
    def add_keyword(self, dictionary_name: str, subcategory: str, keyword: str, persona: str = None, check_conflicts: bool = True) -> bool:
        """
        Add a keyword to a subcategory with improved conflict checking.
        
        Args:
            dictionary_name: Name of the dictionary
            subcategory: Name of the subcategory
            keyword: Keyword to add
            persona: Persona name for categories dictionary (optional)
            check_conflicts: Whether to check for conflicts before adding
            
        Returns:
            True if successful, False otherwise
        """
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        # Clean up the keyword
        keyword = keyword.strip().lower()
        
        if not keyword:
            return False
        
        # Check if keyword already exists in the target subcategory
        try:
            existing_keywords = self.get_keywords(dictionary_name, subcategory, persona)
            existing_keywords_lower = [k.lower() for k in existing_keywords]
            if keyword in existing_keywords_lower:
                print(f"Keyword '{keyword}' already exists.")
                return False
        except:
            # If subcategory doesn't exist yet, that's fine
            pass
        
        # Check for conflicts if requested
        if check_conflicts:
            # Check for conflicts within the appropriate scope
            if dictionary_name == "categories":
                # For categories: Only check within the same persona
                conflicts = self.find_keyword_conflicts(dictionary_name, keyword, subcategory, persona)
            else:
                # For merchants/transaction_types: Check globally within the dictionary
                conflicts = self.find_keyword_conflicts(dictionary_name, keyword, subcategory)
            
            # Show cross-dictionary conflicts as warnings (not blocking)
            cross_conflicts = self.find_cross_dictionary_conflicts(keyword, dictionary_name, persona)
            if cross_conflicts:
                print(f"\nWARNING: '{keyword}' also exists in other dictionaries:")
                print(self.get_conflict_summary(cross_conflicts))
                print("This may cause classification conflicts during transaction parsing.")
            
            # Handle conflicts within the same scope (blocking)
            if conflicts:
                if not self.prompt_user_for_conflict_resolution(keyword, conflicts, "add"):
                    return False
        
        try:
            if dictionary_name == "categories":
                if not persona:
                    raise ValueError("Persona must be provided for categories dictionary")
                
                # Create persona if it doesn't exist
                if persona not in dictionary:
                    dictionary[persona] = {}
                
                # Create subcategory if it doesn't exist
                if subcategory not in dictionary[persona]:
                    dictionary[persona][subcategory] = []
                
                # Add keyword (we already checked it doesn't exist)
                dictionary[persona][subcategory].append(keyword)
            else:
                # Create subcategory if it doesn't exist
                if subcategory not in dictionary:
                    dictionary[subcategory] = []
                
                # Add keyword (we already checked it doesn't exist)
                dictionary[subcategory].append(keyword)
            
            return True
        except Exception as e:
            print(f"Error adding keyword: {e}")
            return False
    
    def remove_keyword(self, dictionary_name: str, subcategory: str, keyword: str, persona: str = None) -> bool:
        """
        Remove a keyword from a subcategory.
        
        Args:
            dictionary_name: Name of the dictionary
            subcategory: Name of the subcategory
            keyword: Keyword to remove
            persona: Persona name for categories dictionary (optional)
            
        Returns:
            True if successful, False otherwise
        """
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        # Clean up the keyword
        keyword = keyword.strip().lower()
        
        try:
            if dictionary_name == "categories":
                if not persona:
                    raise ValueError("Persona must be provided for categories dictionary")
                
                if persona in dictionary and subcategory in dictionary[persona]:
                    # Find the keyword with case-insensitive comparison
                    keywords = dictionary[persona][subcategory]
                    for i, k in enumerate(keywords):
                        if k.lower() == keyword:
                            keywords.pop(i)
                            return True
            else:
                if subcategory in dictionary:
                    # Find the keyword with case-insensitive comparison
                    keywords = dictionary[subcategory]
                    for i, k in enumerate(keywords):
                        if k.lower() == keyword:
                            keywords.pop(i)
                            return True
            
            # Keyword not found
            return False
        except Exception as e:
            print(f"Error removing keyword: {e}")
            return False
    
    def add_subcategory(self, dictionary_name: str, subcategory: str, persona: str = None, check_conflicts: bool = True) -> bool:
        """
        Add a new subcategory to a dictionary with conflict checking.
        
        Args:
            dictionary_name: Name of the dictionary
            subcategory: Name of the subcategory to add
            persona: Persona name for categories dictionary (optional)
            check_conflicts: Whether to check for conflicts before adding
            
        Returns:
            True if successful, False otherwise
        """
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        # Clean up the subcategory name
        subcategory = subcategory.strip().lower()
        
        if not subcategory:
            return False
        
        # Check for conflicts if requested
        if check_conflicts:
            conflicts = self.find_subcategory_conflicts(dictionary_name, subcategory, persona)
            
            if conflicts:
                print(f"\nCONFLICT: Subcategory '{subcategory}' already exists:")
                print(self.get_conflict_summary(conflicts))
                
                proceed = input(f"\nDo you want to proceed anyway? (y/n): ").strip().lower()
                if proceed != 'y':
                    return False
        
        try:
            if dictionary_name == "categories":
                if not persona:
                    raise ValueError("Persona must be provided for categories dictionary")
                
                # Create persona if it doesn't exist
                if persona not in dictionary:
                    dictionary[persona] = {}
                
                # Add subcategory if it doesn't already exist
                if subcategory not in dictionary[persona]:
                    dictionary[persona][subcategory] = []
            else:
                # Add subcategory if it doesn't already exist
                if subcategory not in dictionary:
                    dictionary[subcategory] = []
            
            return True
        except Exception as e:
            print(f"Error adding subcategory: {e}")
            return False
    
    def add_persona(self, persona: str, check_conflicts: bool = True) -> bool:
        """
        Add a new persona to the categories dictionary.
        
        Args:
            persona: Name of the persona to add
            check_conflicts: Whether to check for conflicts before adding
            
        Returns:
            True if successful, False otherwise
        """
        # Clean up the persona name
        persona = persona.strip().lower()
        
        if not persona:
            return False
        
        # Check for conflicts if requested
        if check_conflicts and persona in self.categories:
            print(f"\nCONFLICT: Persona '{persona}' already exists in categories dictionary.")
            proceed = input(f"Do you want to proceed anyway? (y/n): ").strip().lower()
            if proceed != 'y':
                return False
        
        try:
            # Add persona if it doesn't already exist
            if persona not in self.categories:
                self.categories[persona] = {}
            
            return True
        except Exception as e:
            print(f"Error adding persona: {e}")
            return False
    
    def remove_subcategory(self, dictionary_name: str, subcategory: str, persona: str = None) -> bool:
        """
        Remove a subcategory from a dictionary.
        
        Args:
            dictionary_name: Name of the dictionary
            subcategory: Name of the subcategory to remove
            persona: Persona name for categories dictionary (optional)
            
        Returns:
            True if successful, False otherwise
        """
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        try:
            if dictionary_name == "categories":
                if not persona:
                    raise ValueError("Persona must be provided for categories dictionary")
                
                if persona in dictionary and subcategory in dictionary[persona]:
                    del dictionary[persona][subcategory]
                    return True
            else:
                if subcategory in dictionary:
                    del dictionary[subcategory]
                    return True
            
            # Subcategory not found
            return False
        except Exception as e:
            print(f"Error removing subcategory: {e}")
            return False
    
    def remove_persona(self, persona: str) -> bool:
        """
        Remove a persona from the categories dictionary.
        
        Args:
            persona: Name of the persona to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if persona in self.categories:
                del self.categories[persona]
                return True
            
            # Persona not found
            return False
        except Exception as e:
            print(f"Error removing persona: {e}")
            return False