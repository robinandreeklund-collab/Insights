"""Category Manager - Manage custom categories and subcategories."""

import os
import yaml
from typing import Dict, List


class CategoryManager:
    """Manage categories and subcategories for transaction categorization."""
    
    def __init__(self, yaml_dir: str = "yaml"):
        """Initialize the CategoryManager.
        
        Args:
            yaml_dir: Directory where category data is stored
        """
        self.yaml_dir = yaml_dir
        self.categories_file = os.path.join(yaml_dir, "categories.yaml")
        
        # Default categories
        self.default_categories = {
            'Mat & Dryck': ['Matinköp', 'Restaurang', 'Café'],
            'Transport': ['Bränsle & Parkering', 'Kollektivtrafik', 'Taxi'],
            'Boende': ['Hyra & Räkningar', 'Hemförsäkring', 'El'],
            'Shopping': ['Kläder', 'Elektronik', 'Hem & Trädgård'],
            'Nöje': ['Bio & Teater', 'Sport', 'Hobby'],
            'Lån': ['Amortering', 'Ränta', 'Lånebetalning'],
            'Övrigt': ['Okategoriserat', 'Transaktioner', 'Avgifter']
        }
        
        # Ensure directory exists
        os.makedirs(yaml_dir, exist_ok=True)
        
        # Initialize categories file if it doesn't exist
        if not os.path.exists(self.categories_file):
            self._save_categories(self.default_categories)
    
    def _load_yaml(self, filepath: str) -> Dict:
        """Load data from YAML file."""
        if not os.path.exists(filepath):
            return {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _save_yaml(self, filepath: str, data: Dict):
        """Save data to YAML file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
    
    def _save_categories(self, categories: Dict[str, List[str]]):
        """Save categories to file."""
        self._save_yaml(self.categories_file, {'categories': categories})
    
    def get_categories(self) -> Dict[str, List[str]]:
        """Get all categories and their subcategories.
        
        Returns:
            Dictionary mapping category names to lists of subcategories
        """
        data = self._load_yaml(self.categories_file)
        categories = data.get('categories', self.default_categories)
        
        # Ensure all default categories exist
        modified = False
        for cat, subcats in self.default_categories.items():
            if cat not in categories:
                categories[cat] = subcats
                modified = True
        
        if modified:
            self._save_categories(categories)
        
        return categories
    
    def add_category(self, category_name: str, subcategories: List[str] = None) -> bool:
        """Add a new category.
        
        Args:
            category_name: Name of the new category
            subcategories: Optional list of subcategories (defaults to empty list)
            
        Returns:
            True if category was added, False if it already exists
        """
        if not category_name or not category_name.strip():
            return False
        
        categories = self.get_categories()
        
        # Check if category already exists
        if category_name in categories:
            return False
        
        # Add new category
        categories[category_name] = subcategories or []
        self._save_categories(categories)
        
        return True
    
    def add_subcategory(self, category_name: str, subcategory_name: str) -> bool:
        """Add a subcategory to an existing category.
        
        Args:
            category_name: Name of the category
            subcategory_name: Name of the subcategory to add
            
        Returns:
            True if subcategory was added, False if category doesn't exist or subcategory already exists
        """
        if not subcategory_name or not subcategory_name.strip():
            return False
        
        categories = self.get_categories()
        
        # Check if category exists
        if category_name not in categories:
            return False
        
        # Check if subcategory already exists
        if subcategory_name in categories[category_name]:
            return False
        
        # Add subcategory
        categories[category_name].append(subcategory_name)
        self._save_categories(categories)
        
        return True
    
    def remove_category(self, category_name: str) -> bool:
        """Remove a category.
        
        Args:
            category_name: Name of the category to remove
            
        Returns:
            True if category was removed, False if it doesn't exist or is a default category
        """
        # Don't allow removing default categories
        if category_name in self.default_categories:
            return False
        
        categories = self.get_categories()
        
        if category_name not in categories:
            return False
        
        del categories[category_name]
        self._save_categories(categories)
        
        return True
    
    def remove_subcategory(self, category_name: str, subcategory_name: str) -> bool:
        """Remove a subcategory from a category.
        
        Args:
            category_name: Name of the category
            subcategory_name: Name of the subcategory to remove
            
        Returns:
            True if subcategory was removed, False otherwise
        """
        categories = self.get_categories()
        
        if category_name not in categories:
            return False
        
        if subcategory_name not in categories[category_name]:
            return False
        
        categories[category_name].remove(subcategory_name)
        self._save_categories(categories)
        
        return True
    
    def reset_to_defaults(self) -> bool:
        """Reset categories to default values.
        
        Returns:
            True if reset was successful
        """
        self._save_categories(self.default_categories)
        return True
