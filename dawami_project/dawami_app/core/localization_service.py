import json
import os

class LocalizationService:
    def __init__(self, language_code='ar', default_language='en'):
        # Determine the base path for i18n files relative to this file's location
        # dawami_app/core/localization_service.py -> dawami_app/i18n/
        self.i18n_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'i18n')
        self.language_code = language_code
        self.default_language = default_language
        self.translations = {}
        self.load_translations(self.language_code)

    def load_translations(self, language_code):
        """Loads translations for the given language code."""
        file_path = os.path.join(self.i18n_dir, f"{language_code}.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            print(f"Successfully loaded translations for '{language_code}' from {file_path}")
        except FileNotFoundError:
            print(f"Warning: Translation file not found for language '{language_code}' at {file_path}.")
            if language_code != self.default_language:
                print(f"Falling back to default language '{self.default_language}'.")
                self.load_translations(self.default_language) # Attempt to load default
                # Set current lang to default if fallback occurs, to avoid repeated attempts for missing main lang
                self.language_code = self.default_language 
            else:
                # If default language file is also missing, we operate with empty translations
                print(f"Error: Default translation file '{self.default_language}.json' also not found.")
                self.translations = {} 
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from translation file for language '{language_code}'.")
            self.translations = {} # Operate with empty translations on error

    def get_string(self, key, default_value=None):
        """
        Returns the translated string for the given key.
        If key is not found, returns default_value or the key itself if no default_value.
        """
        translation = self.translations.get(key)
        if translation is not None:
            return translation
        
        # If key not found and default_value is provided, return it
        if default_value is not None:
            return default_value
        
        # If key not found and no default_value, return the key itself as a fallback
        # This helps in identifying missing translations during development.
        print(f"Warning: Translation key '{key}' not found for language '{self.language_code}'. Returning key itself.")
        return key

    def set_language(self, language_code):
        """Sets the current language and reloads translations."""
        print(f"Setting language to '{language_code}'")
        self.language_code = language_code
        self.load_translations(language_code)

    def get_current_language(self):
        """Returns the current language code."""
        return self.language_code

if __name__ == '__main__':
    # Example Usage
    # This assumes the script is run from a context where the relative path to i18n works,
    # e.g., from the project root or if dawami_app is in PYTHONPATH.
    
    # For direct testing, adjust path if necessary or ensure i18n dir is discoverable
    # Example: if i18n_dir was just 'i18n', it would look in dawami_app/core/i18n/
    
    print(f"i18n directory should be: {os.path.join(os.path.dirname(os.path.dirname(__file__)), 'i18n')}")

    translator = LocalizationService(language_code='en')
    print(f"\nCurrent language: {translator.get_current_language()}")
    print(f"login.username: {translator.get_string('login.username')}")
    print(f"login.password: {translator.get_string('login.password')}")
    print(f"non.existent.key: {translator.get_string('non.existent.key')}")
    print(f"non.existent.key with default: {translator.get_string('non.existent.key', default_value='Default Text')}")

    translator.set_language('ar')
    print(f"\nCurrent language: {translator.get_current_language()}")
    print(f"login.username (ar): {translator.get_string('login.username')}")
    print(f"login.password (ar): {translator.get_string('login.password')}")

    print("\nTesting fallback for non-existent language:")
    translator.set_language('xx') # Non-existent language
    print(f"Current language after trying 'xx': {translator.get_current_language()}") # Should fall back to 'en'
    print(f"login.button (after fallback): {translator.get_string('login.button')}")

    # Test case where default language file is also missing (manual test by renaming en.json temporarily)
    # print("\nTesting fallback when default language is also missing (manual test):")
    # translator_no_default = LocalizationService(language_code='yy', default_language='zz')
    # print(f"login.button (no default): {translator_no_default.get_string('login.button')}")
