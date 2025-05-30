import os
import sys
import json # For manually checking json files if needed, not for service testing itself

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# Imports from the core package where instances are initialized
from dawami_app.core import translator, theme_manager
from dawami_app.backend.services import settings_service # To verify theme persistence

# Define i18n directory for potential manual checks (not used by service directly for testing)
I18N_DIR = os.path.join(PROJECT_ROOT, "dawami_app", "i18n")


def run_database_setup_if_needed():
    """Ensures the database and SystemSettings table exist for theme persistence."""
    db_file = os.path.join(PROJECT_ROOT, "dawami_app", "database", "dawami_dev.db")
    if not os.path.exists(db_file):
        print(f"Database not found at {db_file}. Running setup scripts...")
        try:
            import subprocess
            venv_python = next((p for p in [os.path.join(PROJECT_ROOT, "venv", "bin", "python"), sys.executable] if os.path.exists(p)), sys.executable)
            print(f"Using Python interpreter: {venv_python} for database_setup.py.")
            # Running database_setup.py is enough, seed_data.py not strictly needed for these core services.
            subprocess.run([venv_python, os.path.join(PROJECT_ROOT, "scripts", "database_setup.py")], check=True, cwd=PROJECT_ROOT)
            print("database_setup.py executed successfully.")
        except Exception as e:
            print(f"Error running database_setup.py: {e}. Please ensure it is runnable.")
            # sys.exit(1) # Don't exit if only theme persistence fails, i18n can still be tested
            print("Continuing without guaranteeing theme persistence tests will fully pass.")
    else:
        print(f"Database file found at {db_file}. Theme persistence tests should work.")
    
    # Clear any previously persisted UI theme to ensure clean test for default loading
    print("Clearing any pre-existing 'ui_theme' setting for a clean test start...")
    settings_service.set_setting(theme_manager.THEME_SETTING_KEY, "") # Set to empty or delete


def test_localization_service():
    print("\n--- Testing LocalizationService ---")

    # Initial state (should be 'ar' as set in core/__init__.py)
    print(f"Initial language: {translator.get_current_language()}")
    assert translator.get_current_language() == 'ar'
    assert translator.get_string("login.username") == "اسم المستخدم"
    print(f"  login.username (ar): {translator.get_string('login.username')}")

    # Switch to English
    translator.set_language('en')
    assert translator.get_current_language() == 'en'
    print(f"Language after set_language('en'): {translator.get_current_language()}")
    assert translator.get_string("login.username") == "Username"
    print(f"  login.username (en): {translator.get_string('login.username')}")
    assert translator.get_string("menu.leave") == "Leave Management"
    print(f"  menu.leave (en): {translator.get_string('menu.leave')}")

    # Test non-existent key
    non_existent_key = "app.feature.new_button"
    assert translator.get_string(non_existent_key) == non_existent_key # Should return key itself
    print(f"  {non_existent_key} (en, non-existent): {translator.get_string(non_existent_key)}")
    assert translator.get_string(non_existent_key, "Default Button") == "Default Button"
    print(f"  {non_existent_key} (en, non-existent with default): {translator.get_string(non_existent_key, 'Default Button')}")

    # Switch back to Arabic
    translator.set_language('ar')
    assert translator.get_current_language() == 'ar'
    print(f"Language after set_language('ar'): {translator.get_current_language()}")
    assert translator.get_string("menu.leave") == "إدارة الإجازات"
    print(f"  menu.leave (ar): {translator.get_string('menu.leave')}")

    # Test loading a non-existent language (should fall back to default 'en')
    print("\nTesting non-existent language 'xx' (should fall back to 'en')...")
    translator.set_language('xx')
    assert translator.get_current_language() == 'en' # Assuming 'en' is the default_language in LocalizationService
    print(f"  Language after trying 'xx': {translator.get_current_language()}")
    assert translator.get_string("login.button") == "Login" # Check with an English string
    print(f"  login.button (after fallback from 'xx'): {translator.get_string('login.button')}")
    
    # Reset to 'ar' for subsequent tests if any depend on global state
    translator.set_language('ar') 
    print("\nLocalizationService tests passed.")

def test_theme_service():
    print("\n--- Testing ThemeService ---")
    
    # Initial theme manager instance (from core init), after clearing ui_theme setting
    # The ThemeService in core was initialized once. We re-init here for a controlled test.
    # Or, better, use the global theme_manager and ensure its state is what we expect.
    
    # To test initial loading from settings properly, we'd ideally re-initialize theme_manager
    # or ensure the setting was cleared *before* core/__init__.py ran.
    # For this test script, let's create a new instance to simulate fresh app start after clearing.
    
    print("Creating a new ThemeService instance for a clean settings load test...")
    # Clear the setting again just before this specific test part
    settings_service.set_setting(theme_manager.THEME_SETTING_KEY, "") 
    # Simulate re-initialization like at app startup
    # This is a bit of a hack for testing the constructor's load path;
    # in a real app, theme_manager is a singleton from core.
    test_theme_manager = type(theme_manager)(default_theme='light') 


    print(f"Initial theme (test_theme_manager, default 'light'): {test_theme_manager.get_theme()}")
    assert test_theme_manager.get_theme() == 'light'
    
    # Set theme to dark
    test_theme_manager.set_theme('dark')
    assert test_theme_manager.get_theme() == 'dark'
    print(f"  Theme after set_theme('dark'): {test_theme_manager.get_theme()}")
    assert settings_service.get_setting(theme_manager.THEME_SETTING_KEY) == 'dark'
    print(f"  Persisted theme in settings: {settings_service.get_setting(theme_manager.THEME_SETTING_KEY)}")

    # Set theme to light
    test_theme_manager.set_theme('light')
    assert test_theme_manager.get_theme() == 'light'
    print(f"  Theme after set_theme('light'): {test_theme_manager.get_theme()}")
    assert settings_service.get_setting(theme_manager.THEME_SETTING_KEY) == 'light'
    print(f"  Persisted theme in settings: {settings_service.get_setting(theme_manager.THEME_SETTING_KEY)}")

    # Test persistence: Create another new instance, should load 'light' from settings
    print("\nCreating another new ThemeService instance to verify loading persisted 'light' theme...")
    test_theme_manager_2 = type(theme_manager)(default_theme='dark') # default to dark to see if light is loaded
    assert test_theme_manager_2.get_theme() == 'light'
    print(f"  Theme loaded by new instance (should be 'light'): {test_theme_manager_2.get_theme()}")
    
    # Test invalid theme name
    print("\nTesting invalid theme name...")
    current_theme_before_invalid = test_theme_manager_2.get_theme()
    test_theme_manager_2.set_theme('purple') # Invalid
    assert test_theme_manager_2.get_theme() == current_theme_before_invalid # Should not change
    print(f"  Theme after trying to set 'purple' (should remain '{current_theme_before_invalid}'): {test_theme_manager_2.get_theme()}")

    # Test get_theme_colors (basic check)
    print("\nTesting get_theme_colors...")
    test_theme_manager_2.set_theme('light')
    light_colors = test_theme_manager_2.get_theme_colors()
    assert light_colors['background'] == '#FFFFFF'
    print(f"  Light theme colors (sample background): {light_colors['background']}")
    
    test_theme_manager_2.set_theme('dark')
    dark_colors = test_theme_manager_2.get_theme_colors()
    assert dark_colors['background'] == '#2B2B2B'
    print(f"  Dark theme colors (sample background): {dark_colors['background']}")

    # Reset to light for global state if needed by other tests (though this test uses local instances)
    # settings_service.set_setting(theme_manager.THEME_SETTING_KEY, "light")
    print("\nThemeService tests passed.")


if __name__ == "__main__":
    print("--- Starting i18n and Theme Management Test ---")
    run_database_setup_if_needed() # For theme persistence
    test_localization_service()
    test_theme_service()
    print("\n--- i18n and Theme Management Test Completed Successfully ---")
