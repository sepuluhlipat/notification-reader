"""
Persona Manager for transaction categorization system.
Allows users to select and apply predefined persona dictionaries to customize their categorization.
"""
import json
import os
from typing import Dict, List, Any, Optional
from dictionary_updater import DictionaryUpdater


class PersonaManager:
    """Manages persona-based dictionary selection and application."""
    
    def __init__(self, dictionary_module=None):
        """Initialize the persona manager."""
        self.dictionary_module = dictionary_module
        self.updater = DictionaryUpdater(dictionary_module)
        
        # Define path to the personas JSON file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self._personas_file_path = os.path.join(current_dir, 'dictionary\personas.json')
        
        self._load_personas()
    
    def _load_personas(self) -> None:
        """Load available personas from the personas JSON file."""
        try:
            with open(self._personas_file_path, 'r', encoding='utf-8') as file:
                self.personas = json.load(file)
        except Exception as e:
            print(f"Error loading personas file: {e}")
            self.personas = self._get_default_personas()
            self._save_personas()
    
    def _save_personas(self) -> bool:
        """Save personas to the JSON file."""
        try:
            with open(self._personas_file_path, 'w', encoding='utf-8') as file:
                json.dump(self.personas, file, indent=2)
            return True
        except Exception as e:
            print(f"Error saving personas file: {e}")
            return False
    
    def _get_default_personas(self) -> Dict:
        """Get default persona definitions based on your existing personas.json structure."""
        return {
            "student": {
                "education": [
                    "tuition", "textbooks", "course materials", "supplies", "class", "university",
                    "school", "college", "books", "study", "library", "exam", "registration", "lab fee"
                ],
                "housing": [
                    "rent", "utilities", "dorm fees", "apartment", "accommodation", "electricity",
                    "water", "dormitory", "wifi", "mobile data", "dorm fees"
                ],
                "food": [
                    "meal plan", "groceries", "dining out", "cafeteria", "canteen", "fast food",
                    "restaurant", "gofood", "lunch", "dinner", "breakfast", "campus food"
                ],
                "transport": [
                    "bus pass", "rideshare", "fuel", "transit", "subway", "train", "grab",
                    "gocar", "commute", "motorcycle", "parking", "campus shuttle", "public transport"
                ],
                "entertainment": [
                    "movie", "game", "streaming", "music", "concert", "hobby", "sports",
                    "netflix", "spotify", "youtube premium", "gaming"
                ],
                "health": [
                    "medicine", "doctor", "clinic", "pharmacy", "hospital", "health insurance",
                    "medical checkup", "dental", "gym membership", "supplements"
                ],
                "shopping": [
                    "clothes", "electronics", "personal care", "cosmetics", "accessories",
                    "gadgets", "fashion", "shoes", "hygiene", "laundry", "toiletries"
                ],
                "finance": [
                    "scholarship", "part-time work", "allowance", "ta position", "grant",
                    "stipend", "award", "fellowship", "savings", "bank", "credit card"
                ]
            },
            "professional": {
                "business": [
                    "office", "supplies", "meeting", "conference", "professional", "networking",
                    "coworking", "business cards", "presentations", "development", "certification"
                ],
                "dining": [
                    "restaurant", "cafe", "lunch", "dinner", "business meal", "food delivery",
                    "client dinner", "team lunch", "coffee", "work lunch"
                ],
                "transport": [
                    "taxi", "grab", "gojek", "fuel", "parking", "toll", "car maintenance",
                    "public transport", "business travel", "car payment"
                ],
                "travel": [
                    "hotel", "flight", "accommodation", "business trip", "vacation", "airline",
                    "booking", "travel insurance"
                ],
                "finance": [
                    "stocks", "mutual fund", "savings", "insurance", "investment", "trading",
                    "retirement fund", "portfolio", "banking", "loans", "credit card", "taxes"
                ],
                "bills": [
                    "internet", "phone", "electricity", "water", "gas", "subscription",
                    "software", "cloud services"
                ],
                "health": [
                    "insurance", "medical", "doctor", "pharmacy", "fitness", "gym",
                    "wellness", "health checkup"
                ],
                "shopping": [
                    "clothes", "electronics", "home", "personal care", "gifts",
                    "professional attire", "gadgets"
                ],
                "entertainment": [
                    "movie", "streaming", "music", "books", "hobbies", "sports", "weekend activities"
                ]
            },
            "family": {
                "groceries": [
                    "supermarket", "grocery", "vegetables", "meat", "dairy", "household items",
                    "cleaning", "weekly shopping", "bulk buying"
                ],
                "children": [
                    "school", "education", "toys", "clothes", "baby", "diapers", "childcare",
                    "tuition", "school supplies", "kids activities"
                ],
                "housing": [
                    "mortgage", "rent", "maintenance", "property tax", "repairs", "renovation",
                    "home improvement", "furniture", "appliances", "home decor", "garden"
                ],
                "food": [
                    "restaurant", "family meal", "takeout", "delivery", "cafe", "fast food",
                    "family outing", "celebration", "school lunches"
                ],
                "transport": [
                    "car", "fuel", "maintenance", "insurance", "family trip", "school transport",
                    "car payment", "family vehicle"
                ],
                "health": [
                    "medical", "pharmacy", "insurance", "family doctor", "dental", "family health",
                    "pediatrician", "family medicine"
                ],
                "entertainment": [
                    "family outing", "movie", "park", "vacation", "family activities", "sports",
                    "amusement park", "family fun"
                ],
                "bills": [
                    "electricity", "water", "gas", "internet", "phone", "cable", "insurance", "home services"
                ],
                "finance": [
                    "emergency fund", "family savings", "children's future", "education fund",
                    "family insurance", "college fund", "retirement"
                ]
            },
            "entrepreneur": {
                "operations": [
                    "office rent", "supplies", "equipment", "software", "tools", "workspace",
                    "inventory", "production", "rent", "utilities"
                ],
                "marketing": [
                    "advertising", "promotion", "social media", "website", "branding",
                    "marketing tools", "campaigns", "seo", "events"
                ],
                "networking": [
                    "events", "conferences", "meetings", "business meals", "professional development",
                    "workshops", "seminars"
                ],
                "finance": [
                    "business investment", "equipment", "technology", "expansion", "assets",
                    "startup costs", "capital", "business loans", "credit", "taxes"
                ],
                "travel": [
                    "business travel", "client meetings", "conferences", "accommodation",
                    "transportation", "trade shows"
                ],
                "services": [
                    "legal", "accounting", "consulting", "banking", "insurance", "advisory",
                    "professional fees", "bookkeeping", "licenses"
                ],
                "staff": [
                    "salaries", "benefits", "team building", "training", "recruitment",
                    "contractor fees", "payroll", "compensation"
                ],
                "transport": [
                    "business travel", "client visits", "uber", "grab", "public transport", "fuel"
                ],
                "food": [
                    "meals", "coffee", "work meals", "client lunches", "food delivery", "business meals"
                ]
            },
            "minimalist": {
                "essentials": [
                    "food", "groceries", "basic meals", "necessities", "survival", "basic needs", "staples"
                ],
                "housing": [
                    "rent", "utilities", "electricity", "water", "gas", "internet", "basic services", "housing"
                ],
                "transport": [
                    "public transport", "basic travel", "necessary trips", "commute", "essential travel"
                ],
                "health": [
                    "medical", "pharmacy", "basic healthcare", "essential medicine", "doctor", "health necessities"
                ],
                "finance": [
                    "salary", "earnings", "essential income", "primary income", "work",
                    "emergency fund", "basic savings", "essential reserves"
                ]
            }
        }
    
    def get_available_personas(self) -> List[str]:
        """Get list of available persona IDs."""
        return list(self.personas.keys())
    
    def get_persona_categories(self, persona_id: str) -> Optional[Dict]:
        """Get categories for a specific persona."""
        return self.personas.get(persona_id)
    
    def preview_persona_categories(self, persona_id: str) -> Optional[str]:
        """Generate a preview of persona categories for display."""
        categories = self.get_persona_categories(persona_id)
        if not categories:
            return None
        
        preview = f"\n{'='*60}\n"
        preview += f"PERSONA: {persona_id.upper()}\n"
        preview += f"{'='*60}\n"
        
        total_categories = len(categories)
        total_keywords = sum(len(keywords) for keywords in categories.values())
        preview += f"Statistics: {total_categories} categories, {total_keywords} total keywords\n\n"
        
        preview += "CATEGORIES AND KEYWORDS:\n"
        preview += "-" * 30 + "\n"
        
        for i, (category, keywords) in enumerate(categories.items(), 1):
            preview += f"\n{i}. {category.upper()} ({len(keywords)} keywords):\n"
            
            if len(keywords) <= 8:
                # Show all keywords if 8 or fewer
                keywords_str = ", ".join(keywords)
                preview += f"   {keywords_str}\n"
            else:
                # Show first 8 keywords and indicate more
                keywords_str = ", ".join(keywords[:8])
                remaining = len(keywords) - 8
                preview += f"   {keywords_str}\n"
                preview += f"   ... and {remaining} more keywords\n"
        
        return preview
    
    def get_current_categories_preview(self) -> str:
        """Get a preview of current categories for comparison."""
        try:
            current_categories = self.updater.get_dictionary_section('categories')
            total_categories = len(current_categories)
            total_keywords = sum(len(keywords) for keywords in current_categories.values())
            
            preview = f"\n{'='*60}\n"
            preview += f"CURRENT CATEGORIES\n"
            preview += f"{'='*60}\n"
            preview += f"Statistics: {total_categories} categories, {total_keywords} total keywords\n\n"
            
            preview += "CURRENT CATEGORIES:\n"
            preview += "-" * 20 + "\n"
            
            for i, (category, keywords) in enumerate(current_categories.items(), 1):
                preview += f"\n{i}. {category.upper()} ({len(keywords)} keywords):\n"
                
                if len(keywords) <= 8:
                    keywords_str = ", ".join(keywords)
                    preview += f"   {keywords_str}\n"
                else:
                    keywords_str = ", ".join(keywords[:8])
                    remaining = len(keywords) - 8
                    preview += f"   {keywords_str}\n"
                    preview += f"   ... and {remaining} more keywords\n"
            
            return preview
            
        except Exception as e:
            return f"Error loading current categories: {e}"
    
    def apply_persona_categories(self, persona_id: str, backup_current: bool = True) -> bool:
        """Apply a persona's categories to replace current categories."""
        persona_categories = self.get_persona_categories(persona_id)
        if not persona_categories:
            print(f"Persona '{persona_id}' not found.")
            return False
        
        try:
            # Backup current categories if requested
            if backup_current:
                self._backup_current_categories()
            
            # Replace the categories dictionary
            self.updater.dictionaries['categories'] = persona_categories.copy()
            
            # Save changes
            if self.updater.save_changes():
                print(f"\nPersona '{persona_id}' categories applied successfully!")
                print(f"Applied {len(persona_categories)} categories with {sum(len(k) for k in persona_categories.values())} total keywords.")
                return True
            else:
                print("Failed to save persona categories.")
                return False
                
        except Exception as e:
            print(f"Error applying persona categories: {e}")
            return False
    
    def _backup_current_categories(self) -> bool:
        """Create a backup of current categories."""
        try:
            current_categories = self.updater.get_dictionary_section('categories')
            
            # Create backup file with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"categories_backup_{timestamp}.json"
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backup_path = os.path.join(current_dir, 'backups', backup_filename)
            
            # Create backups directory if it doesn't exist
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            with open(backup_path, 'w', encoding='utf-8') as file:
                json.dump(current_categories, file, indent=2)
            
            print(f"Current categories backed up to: {backup_filename}")
            return True
            
        except Exception as e:
            print(f"Warning: Failed to backup current categories: {e}")
            return False
    
    def run_persona_selector(self):
        """Interactive persona selection interface."""
        print("\n" + "=" * 60)
        print("PERSONA SELECTOR")
        print("Choose a persona to customize your transaction categories")
        print("=" * 60)
        
        while True:
            choice = self._get_persona_menu_choice()
            
            if choice == "1":
                self._show_available_personas()
            elif choice == "2":
                if not self._select_and_preview_persona():
                    break
            elif choice == "3":
                self._show_current_categories()
            elif choice == "4":
                print("\nExiting persona selector.")
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def _get_persona_menu_choice(self) -> str:
        """Display persona selector main menu."""
        print(f"\n{'='*50}")
        print("PERSONA SELECTOR MENU")
        print("1. Show available personas")
        print("2. Select and apply persona")
        print("3. View current categories")
        print("4. Exit")
        return input("\nEnter your choice [1-4]: ").strip()
    
    def _show_available_personas(self):
        """Display all available personas."""
        personas = self.get_available_personas()
        
        print(f"\n{'='*60}")
        print("AVAILABLE PERSONAS")
        print(f"{'='*60}")
        
        for i, persona_id in enumerate(personas, 1):
            categories = self.get_persona_categories(persona_id)
            total_categories = len(categories)
            total_keywords = sum(len(keywords) for keywords in categories.values())
            
            print(f"\n{i}. {persona_id.upper()}")
            print(f"   Categories: {total_categories}, Keywords: {total_keywords}")
        
        input("\nPress Enter to continue...")
    
    def _show_current_categories(self):
        """Display current categories."""
        preview = self.get_current_categories_preview()
        print(preview)
        input("\nPress Enter to continue...")
    
    def _select_and_preview_persona(self) -> bool:
        """Select a persona, preview it, and optionally apply it."""
        personas = self.get_available_personas()
        
        if not personas:
            print("\nNo personas available.")
            return True
        
        print(f"\n{'='*50}")
        print("SELECT PERSONA")
        print(f"{'='*50}")
        
        for i, persona_id in enumerate(personas, 1):
            print(f"{i}. {persona_id.title()}")
        
        try:
            choice = input(f"\nSelect persona [1-{len(personas)}] or 'back' to return: ").strip()
            
            if choice.lower() == 'back':
                return True
            
            persona_idx = int(choice) - 1
            if 0 <= persona_idx < len(personas):
                selected_persona = personas[persona_idx]
                return self._preview_and_apply_persona(selected_persona)
            else:
                print("\nInvalid persona number.")
                
        except ValueError:
            print("\nPlease enter a valid persona number.")
        
        return True
    
    def _preview_and_apply_persona(self, persona_id: str) -> bool:
        """Preview a persona and ask user if they want to apply it."""
        # Show persona preview
        preview = self.preview_persona_categories(persona_id)
        if not preview:
            print(f"\nError loading persona '{persona_id}'.")
            return True
        
        # Display the preview
        print(preview)
        
        # Show current categories for comparison
        print("\n" + "=" * 60)
        print("COMPARISON WITH CURRENT CATEGORIES")
        print("=" * 60)
        current_preview = self.get_current_categories_preview()
        print(current_preview)
        
        # Ask user if they want to apply
        print(f"\n{'='*60}")
        print("APPLY PERSONA?")
        print(f"{'='*60}")
        print("This will REPLACE your current categories with the selected persona's categories.")
        print("Your current categories will be backed up automatically.")
        
        while True:
            choice = input("\nDo you want to apply this persona? (y/n/back): ").strip().lower()
            
            if choice == 'y' or choice == 'yes':
                if self.apply_persona_categories(persona_id):
                    print(f"\nPersona '{persona_id}' has been applied successfully!")
                    print("You can now use the dictionary updater to further customize your categories.")
                    input("\nPress Enter to continue...")
                    return False  # Exit to main menu
                else:
                    print("\nFailed to apply persona. Please try again.")
                    return True
                    
            elif choice == 'n' or choice == 'no':
                print("\nPersona not applied. Returning to selection.")
                return True
                
            elif choice == 'back':
                return True
                
            else:
                print("Please enter 'y' for yes, 'n' for no, or 'back' to return.")


def run_persona_selector():
    """Convenience function to run the persona selector."""
    manager = PersonaManager()
    manager.run_persona_selector()