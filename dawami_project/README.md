# Dawami Project

This project is for the Dawami system.

## Setup

1.  **Initialize Virtual Environment:**
    `python3 -m venv venv`
2.  **Activate Virtual Environment:**
    `source venv/bin/activate` (on Linux/macOS) or `venv\\Scripts\\activate` (on Windows)
3.  **Install Dependencies:**
    `pip install -r requirements.txt` (A requirements.txt file will be added later)

## Running the Application

`python main.py`

## Project Structure

-   `dawami_app/`: Main application code.
    -   `frontend/`: User interface components.
        -   `assets/`: Static files (images, fonts).
        -   `widgets/`: Custom UI widgets.
        -   `views/`: Application views/screens.
    -   `backend/`: Server-side logic.
        -   `services/`: Business logic and services.
        -   `database/`: Database related modules.
            -   `models/`: Database models/schemas.
            -   `migrations/`: Database migration scripts.
    -   `core/`: Shared utilities, constants.
    -   `i18n/`: Localization files.
-   `tests/`: Unit and integration tests.
-   `docs/`: Project documentation.
-   `scripts/`: Utility scripts.
-   `main.py`: Application entry point.
-   `config.ini`: Application configuration.
-   `venv/`: Python virtual environment.
-   `.gitignore`: Specifies intentionally untracked files that Git should ignore.
-   `README.md`: This file.
