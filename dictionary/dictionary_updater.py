"""
Dictionary updater module for the transaction categorization system.
Allows users to view and edit dictionary entries and save changes to JSON files.
"""
import json
import os
from typing import Dict, List, Any, Tuple, Optional

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
    
    def add_keyword(self, dictionary_name: str, subcategory: str, keyword: str, persona: str = None) -> bool:
        """
        Add a keyword to a subcategory.
        
        Args:
            dictionary_name: Name of the dictionary
            subcategory: Name of the subcategory
            keyword: Keyword to add
            persona: Persona name for categories dictionary (optional)
            
        Returns:
            True if successful, False otherwise
        """
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        # Clean up the keyword
        keyword = keyword.strip().lower()
        
        if not keyword:
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
                
                # Add keyword if it doesn't already exist
                if keyword not in dictionary[persona][subcategory]:
                    dictionary[persona][subcategory].append(keyword)
            else:
                # Create subcategory if it doesn't exist
                if subcategory not in dictionary:
                    dictionary[subcategory] = []
                
                # Add keyword if it doesn't already exist
                if keyword not in dictionary[subcategory]:
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
                    if keyword in dictionary[persona][subcategory]:
                        dictionary[persona][subcategory].remove(keyword)
                        return True
            else:
                if subcategory in dictionary:
                    if keyword in dictionary[subcategory]:
                        dictionary[subcategory].remove(keyword)
                        return True
            
            # Keyword not found
            return False
        except Exception as e:
            print(f"Error removing keyword: {e}")
            return False
    
    def add_subcategory(self, dictionary_name: str, subcategory: str, persona: str = None) -> bool:
        """
        Add a new subcategory to a dictionary.
        
        Args:
            dictionary_name: Name of the dictionary
            subcategory: Name of the subcategory to add
            persona: Persona name for categories dictionary (optional)
            
        Returns:
            True if successful, False otherwise
        """
        dictionary, _ = self.get_dictionary_info(dictionary_name)
        
        # Clean up the subcategory name
        subcategory = subcategory.strip().lower()
        
        if not subcategory:
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
    
    def add_persona(self, persona: str) -> bool:
        """
        Add a new persona to the categories dictionary.
        
        Args:
            persona: Name of the persona to add
            
        Returns:
            True if successful, False otherwise
        """
        # Clean up the persona name
        persona = persona.strip().lower()
        
        if not persona:
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