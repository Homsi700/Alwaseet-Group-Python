# dawami_app/core/__init__.py

# Initialize and expose core services for easier access throughout the application.

from .localization_service import LocalizationService
from .theme_service import ThemeService

# --- Localization Service ---
# Default language is 'ar' as per project specification.
# Fallback language is 'en'.
translator = LocalizationService(language_code='ar', default_language='en')

# --- Theme Service ---
# Default theme is 'light'. It will try to load the persisted theme from settings.
theme_manager = ThemeService(default_theme='light')

# You can add other core functionalities or singletons here as the project grows.

__all__ = [
    'translator',
    'theme_manager'
]

print("Dawami Core Services (translator, theme_manager) initialized.")
