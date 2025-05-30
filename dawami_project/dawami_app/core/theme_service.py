import os
import sys

# Add project root to sys.path to allow importing settings_service
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

# It's better to import the specific service needed rather than the whole module if not all is needed
# However, for simplicity here, or if many settings are managed, importing the module is fine.
from dawami_app.backend.services import settings_service

class ThemeService:
    THEME_SETTING_KEY = 'ui_theme' # Key used to store theme in SystemSettings

    def __init__(self, default_theme='light'):
        self.default_theme = default_theme
        self.current_theme = self._load_theme_from_settings() or default_theme
        print(f"ThemeService initialized. Current theme: '{self.current_theme}' (Loaded from settings if available, else default).")

    def _load_theme_from_settings(self):
        """Loads the theme preference from system settings."""
        persisted_theme = settings_service.get_setting(self.THEME_SETTING_KEY)
        if persisted_theme in ['light', 'dark']: # Add more valid themes if needed
            print(f"Loaded theme '{persisted_theme}' from settings.")
            return persisted_theme
        print(f"No valid theme found in settings for key '{self.THEME_SETTING_KEY}'. Using default.")
        return None

    def set_theme(self, theme_name):
        """
        Sets the current theme and persists it.
        :param theme_name: Name of the theme (e.g., 'light', 'dark').
        """
        if theme_name not in ['light', 'dark']: # Basic validation
            print(f"Warning: Invalid theme name '{theme_name}'. Theme not changed.")
            return

        self.current_theme = theme_name
        print(f"Theme changed to '{self.current_theme}'.")
        
        # Persist this setting
        success = settings_service.set_setting(self.THEME_SETTING_KEY, self.current_theme, "User interface appearance mode (light/dark)")
        if success:
            print(f"Theme preference '{self.current_theme}' saved to settings.")
        else:
            print(f"Warning: Failed to save theme preference '{self.current_theme}' to settings.")
        
        # In a real UI app, you would now typically:
        # 1. Notify UI components to update their appearance.
        # 2. For CustomTkinter: ctk.set_appearance_mode(self.current_theme)

    def get_theme(self):
        """Returns the current theme name."""
        return self.current_theme

    # Example for future expansion:
    def get_theme_colors(self):
        """Returns a dictionary of colors for the current theme."""
        if self.current_theme == 'dark':
            return {
                'background': '#2B2B2B',
                'text': '#FFFFFF',
                'primary': '#0A74DA', # Example blue
                'widget_bg': '#3C3F41',
                'entry_bg': '#313335',
            }
        else: # Light theme (default)
            return {
                'background': '#FFFFFF',
                'text': '#000000',
                'primary': '#3B8ED0', # Example blue
                'widget_bg': '#F0F0F0',
                'entry_bg': '#E8E8E8',
            }

if __name__ == '__main__':
    # Example Usage
    print("Theme Service Module - Direct Execution (for testing)")

    # Ensure settings DB is available for this test
    db_file = os.path.join(PROJECT_ROOT, "dawami_app", "database", "dawami_dev.db")
    if not os.path.exists(db_file):
        print(f"WARNING: Database file not found at {db_file}. Theme persistence tests might fail.")
        print("Please run relevant setup scripts first.")
        # If settings_service cannot connect, it will print errors but not crash ThemeService init.

    # Initialize with default
    theme_manager1 = ThemeService(default_theme='light')
    print(f"Initial theme (manager1): {theme_manager1.get_theme()}")

    # Change and persist
    theme_manager1.set_theme('dark')
    print(f"Theme after set (manager1): {theme_manager1.get_theme()}")
    
    # Verify persistence by creating a new instance
    print("\nCreating second ThemeService instance to test loading from settings...")
    theme_manager2 = ThemeService(default_theme='light') # default is light
    print(f"Initial theme (manager2 - should load from settings): {theme_manager2.get_theme()}")
    assert theme_manager2.get_theme() == 'dark' # Should have loaded 'dark'

    # Change back to light
    theme_manager2.set_theme('light')
    print(f"Theme after set (manager2): {theme_manager2.get_theme()}")

    # Verify persistence again
    print("\nCreating third ThemeService instance...")
    theme_manager3 = ThemeService(default_theme='dark') # default is dark this time
    print(f"Initial theme (manager3 - should load from settings): {theme_manager3.get_theme()}")
    assert theme_manager3.get_theme() == 'light' # Should have loaded 'light'

    print("\nTheme Service direct execution tests completed.")
    print(f"Theme colors for '{theme_manager3.get_theme()}': {theme_manager3.get_theme_colors()}")
