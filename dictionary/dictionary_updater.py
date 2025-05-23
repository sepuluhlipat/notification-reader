"""
Enhanced Dictionary updater module for the transaction categorization system.
Allows users to view and edit dictionary entries and save changes to JSON files.
Includes improved conflict checking with proper scoping for categories.
Shows only the specific conflicting keyword when displaying conflicts.
"""
import json
import os
from typing import Dict, List, Any, Tuple, Optional


class DictionaryUpdater:
    def __init__(self, dictionary_module=None):
        """Initialize the dictionary updater with paths to the JSON files."""
        self.dictionary_module = dictionary_module
        
        # Define paths to JSON files
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self._file_paths = {
            'categories': os.path.join(current_dir, 'categories.json'),
            'merchants': os.path.join(current_dir, 'merchants.json'),
            'transaction_types': os.path.join(current_dir, 'transaction_types.json')
        }
        
        self._load_dictionaries()
    
    def _load_dictionaries(self) -> None:
        """Load all dictionaries from their respective JSON files."""
        if self.dictionary_module:
            self.categories = self.dictionary_module.get_all_categories()
            self.merchants = self.dictionary_module.get_merchants()
            self.transaction_types = self.dictionary_module.get_transaction_types()
        else:
            self.categories = self._load_json_file(self._file_paths['categories'])
            self.merchants = self._load_json_file(self._file_paths['merchants'])
            self.transaction_types = self._load_json_file(self._file_paths['transaction_types'])
    
    def _load_json_file(self, file_path: str) -> Dict:
        """Load data from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading JSON file {file_path}: {e}")
            return {}
    
    def _save_json_file(self, file_path: str, data: Dict) -> bool:
        """Save data to a JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2)
            return True
        except Exception as e:
            print(f"Error saving JSON file {file_path}: {e}")
            return False
    
    def get_dictionary_info(self, dictionary_name: str) -> Tuple[Dict, str]:
        """Get a dictionary and its file path by name."""
        dictionary_map = {
            'categories': (self.categories, self._file_paths['categories']),
            'merchants': (self.merchants, self._file_paths['merchants']),
            'transaction_types': (self.transaction_types, self._file_paths['transaction_types'])
        }
        
        if dictionary_name not in dictionary_map:
            raise ValueError(f"Unknown dictionary: {dictionary_name}")
        
        return dictionary_map[dictionary_name]
    
    def _find_matching_keyword(self, keywords: List[str], target_keyword: str) -> Optional[str]:
        """Find a keyword that matches the target (case-insensitive)."""
        target_lower = target_keyword.lower()
        for keyword in keywords:
            if keyword.lower() == target_lower:
                return keyword
        return None
    
    def find_keyword_conflicts(self, dictionary_name: str, keyword: str, 
                             exclude_subcategory: str = None, exclude_persona: str = None) -> List[Dict[str, str]]:
        """Find all occurrences of a keyword with proper scoping."""
        conflicts = []
        keyword_lower = keyword.strip().lower()
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        if dictionary_name == "categories":
            # For categories: Only search within the same persona
            if exclude_persona and exclude_persona in dictionary:
                persona_dict = dictionary[exclude_persona]
                conflicts.extend(self._search_persona_conflicts(
                    persona_dict, keyword_lower, exclude_subcategory, exclude_persona, dictionary_name
                ))
        else:
            # For merchants and transaction_types: Search globally
            conflicts.extend(self._search_global_conflicts(
                dictionary, keyword_lower, exclude_subcategory, dictionary_name
            ))
        
        return conflicts
    
    def _search_persona_conflicts(self, persona_dict: Dict, keyword_lower: str, 
                                exclude_subcategory: str, persona: str, dictionary_name: str) -> List[Dict[str, str]]:
        """Search for conflicts within a persona."""
        conflicts = []
        for subcategory, keywords in persona_dict.items():
            if exclude_subcategory and subcategory == exclude_subcategory:
                continue
            
            matching_keyword = self._find_matching_keyword(keywords, keyword_lower)
            if matching_keyword:
                conflicts.append({
                    'dictionary': dictionary_name,
                    'persona': persona,
                    'subcategory': subcategory,
                    'conflicting_keyword': matching_keyword,
                    'location': f"{dictionary_name} -> {persona} -> {subcategory}"
                })
        return conflicts
    
    def _search_global_conflicts(self, dictionary: Dict, keyword_lower: str, 
                               exclude_subcategory: str, dictionary_name: str) -> List[Dict[str, str]]:
        """Search for conflicts globally within a dictionary."""
        conflicts = []
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
    
    def find_subcategory_conflicts(self, dictionary_name: str, subcategory: str, 
                                 persona: str = None) -> List[Dict[str, Any]]:
        """Find if a subcategory name exists in other contexts within the same dictionary."""
        conflicts = []
        subcategory_lower = subcategory.strip().lower()
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        if dictionary_name == "categories":
            if persona and persona in dictionary:
                conflicts.extend(self._check_persona_subcategory_conflicts(
                    dictionary[persona], subcategory_lower, persona, dictionary_name
                ))
        else:
            conflicts.extend(self._check_global_subcategory_conflicts(
                dictionary, subcategory_lower, dictionary_name
            ))
        
        return conflicts
    
    def _check_persona_subcategory_conflicts(self, persona_dict: Dict, subcategory_lower: str, 
                                           persona: str, dictionary_name: str) -> List[Dict[str, Any]]:
        """Check for subcategory conflicts within a persona."""
        conflicts = []
        for existing_subcategory, keywords in persona_dict.items():
            if existing_subcategory.lower() == subcategory_lower:
                conflicts.append({
                    'dictionary': dictionary_name,
                    'persona': persona,
                    'subcategory': existing_subcategory,
                    'keywords': keywords,
                    'keywords_count': len(keywords),
                    'location': f"{dictionary_name} -> {persona} -> {existing_subcategory}"
                })
        return conflicts
    
    def _check_global_subcategory_conflicts(self, dictionary: Dict, subcategory_lower: str, 
                                          dictionary_name: str) -> List[Dict[str, Any]]:
        """Check for subcategory conflicts globally within a dictionary."""
        conflicts = []
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
    
    def find_cross_dictionary_conflicts(self, keyword: str, exclude_dictionary: str = None, 
                                      current_persona: str = None) -> List[Dict[str, str]]:
        """Find conflicts across all dictionaries for a given keyword."""
        all_conflicts = []
        keyword_lower = keyword.strip().lower()
        
        for dict_name in ["categories", "merchants", "transaction_types"]:
            if exclude_dictionary and dict_name == exclude_dictionary:
                continue
            
            dictionary, _ = self.get_dictionary_info(dict_name)
            
            if dict_name == "categories":
                # Search across all personas for cross-dictionary warnings
                for persona_name, persona_dict in dictionary.items():
                    all_conflicts.extend(self._search_persona_conflicts(
                        persona_dict, keyword_lower, None, persona_name, dict_name
                    ))
            else:
                # Search globally for merchants and transaction_types
                all_conflicts.extend(self._search_global_conflicts(
                    dictionary, keyword_lower, None, dict_name
                ))
        
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
                
                if conflict['dictionary'] == 'categories':
                    success = self.remove_keyword('categories', conflict['subcategory'], 
                                                keyword_to_remove, conflict['persona'])
                    location = f"categories -> {conflict['persona']} -> {conflict['subcategory']}"
                else:
                    success = self.remove_keyword(conflict['dictionary'], conflict['subcategory'], 
                                                keyword_to_remove)
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
        """Save all dictionaries to their respective JSON files."""
        results = {}
        for dict_name, file_path in self._file_paths.items():
            dictionary, _ = self.get_dictionary_info(dict_name)
            results[dict_name] = self._save_json_file(file_path, dictionary)
        
        # If dictionary module is provided, reload dictionaries
        if self.dictionary_module:
            self.dictionary_module.reload_dictionaries()
            
        return results
    
    def get_available_dictionaries(self) -> List[str]:
        """Get a list of available dictionaries that can be updated."""
        return list(self._file_paths.keys())
    
    def get_subcategories(self, dictionary_name: str, persona: str = None) -> List[str]:
        """Get available subcategories for a given dictionary."""
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        if dictionary_name == "categories":
            if persona and persona in dictionary:
                return list(dictionary[persona].keys())
            elif persona:
                raise ValueError(f"Persona '{persona}' not found in categories dictionary")
            else:
                return list(dictionary.keys())  # Return personas
        else:
            return list(dictionary.keys())
    
    def get_keywords(self, dictionary_name: str, subcategory: str, persona: str = None) -> List[str]:
        """Get keywords for a specific subcategory."""
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
    
    def _keyword_exists_in_subcategory(self, dictionary_name: str, subcategory: str, 
                                     keyword: str, persona: str = None) -> bool:
        """Check if a keyword already exists in a subcategory."""
        try:
            existing_keywords = self.get_keywords(dictionary_name, subcategory, persona)
            return any(k.lower() == keyword.lower() for k in existing_keywords)
        except:
            return False
    
    def add_keyword(self, dictionary_name: str, subcategory: str, keyword: str, 
                   persona: str = None, check_conflicts: bool = True) -> bool:
        """Add a keyword to a subcategory with improved conflict checking."""
        keyword = keyword.strip().lower()
        if not keyword:
            return False
        
        # Check if keyword already exists in the target subcategory
        if self._keyword_exists_in_subcategory(dictionary_name, subcategory, keyword, persona):
            print(f"Keyword '{keyword}' already exists.")
            return False
        
        # Check for conflicts if requested
        if check_conflicts:
            # Check for conflicts within the appropriate scope
            if dictionary_name == "categories":
                conflicts = self.find_keyword_conflicts(dictionary_name, keyword, subcategory, persona)
            else:
                conflicts = self.find_keyword_conflicts(dictionary_name, keyword, subcategory)
            
            # Show cross-dictionary conflicts as warnings
            cross_conflicts = self.find_cross_dictionary_conflicts(keyword, dictionary_name, persona)
            if cross_conflicts:
                print(f"\nWARNING: '{keyword}' also exists in other dictionaries:")
                print(self.get_conflict_summary(cross_conflicts))
                print("This may cause classification conflicts during transaction parsing.")
            
            # Handle conflicts within the same scope
            if conflicts:
                if not self.prompt_user_for_conflict_resolution(keyword, conflicts, "add"):
                    return False
        
        return self._add_keyword_to_dictionary(dictionary_name, subcategory, keyword, persona)
    
    def _add_keyword_to_dictionary(self, dictionary_name: str, subcategory: str, 
                                 keyword: str, persona: str = None) -> bool:
        """Add keyword to the appropriate dictionary structure."""
        try:
            dictionary, _ = self.get_dictionary_info(dictionary_name)
            
            if dictionary_name == "categories":
                if not persona:
                    raise ValueError("Persona must be provided for categories dictionary")
                
                if persona not in dictionary:
                    dictionary[persona] = {}
                
                if subcategory not in dictionary[persona]:
                    dictionary[persona][subcategory] = []
                
                dictionary[persona][subcategory].append(keyword)
            else:
                if subcategory not in dictionary:
                    dictionary[subcategory] = []
                
                dictionary[subcategory].append(keyword)
            
            return True
        except Exception as e:
            print(f"Error adding keyword: {e}")
            return False
    
    def remove_keyword(self, dictionary_name: str, subcategory: str, keyword: str, 
                      persona: str = None) -> bool:
        """Remove a keyword from a subcategory."""
        keyword_lower = keyword.strip().lower()
        
        try:
            dictionary, _ = self.get_dictionary_info(dictionary_name)
            
            if dictionary_name == "categories":
                if not persona or persona not in dictionary or subcategory not in dictionary[persona]:
                    return False
                keywords = dictionary[persona][subcategory]
            else:
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
    
    def add_subcategory(self, dictionary_name: str, subcategory: str, 
                       persona: str = None, check_conflicts: bool = True) -> bool:
        """Add a new subcategory to a dictionary with conflict checking."""
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
        
        return self._add_subcategory_to_dictionary(dictionary_name, subcategory, persona)
    
    def _add_subcategory_to_dictionary(self, dictionary_name: str, subcategory: str, 
                                     persona: str = None) -> bool:
        """Add subcategory to the appropriate dictionary structure."""
        try:
            dictionary, _ = self.get_dictionary_info(dictionary_name)
            
            if dictionary_name == "categories":
                if not persona:
                    raise ValueError("Persona must be provided for categories dictionary")
                
                if persona not in dictionary:
                    dictionary[persona] = {}
                
                if subcategory not in dictionary[persona]:
                    dictionary[persona][subcategory] = []
            else:
                if subcategory not in dictionary:
                    dictionary[subcategory] = []
            
            return True
        except Exception as e:
            print(f"Error adding subcategory: {e}")
            return False
    
    def add_persona(self, persona: str, check_conflicts: bool = True) -> bool:
        """Add a new persona to the categories dictionary."""
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
            if persona not in self.categories:
                self.categories[persona] = {}
            return True
        except Exception as e:
            print(f"Error adding persona: {e}")
            return False
    
    def remove_subcategory(self, dictionary_name: str, subcategory: str, persona: str = None) -> bool:
        """Remove a subcategory from a dictionary."""
        try:
            dictionary, _ = self.get_dictionary_info(dictionary_name)
            
            if dictionary_name == "categories":
                if not persona or persona not in dictionary or subcategory not in dictionary[persona]:
                    return False
                del dictionary[persona][subcategory]
            else:
                if subcategory not in dictionary:
                    return False
                del dictionary[subcategory]
            
            return True
        except Exception as e:
            print(f"Error removing subcategory: {e}")
            return False
    
    def remove_persona(self, persona: str) -> bool:
        """Remove a persona from the categories dictionary."""
        try:
            if persona in self.categories:
                del self.categories[persona]
                return True
            return False
        except Exception as e:
            print(f"Error removing persona: {e}")
            return False