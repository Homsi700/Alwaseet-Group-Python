import os
import sys

# Add project root to sys.path to allow importing from dawami_app
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

# import customtkinter as ctk # GUI Disabled
from dawami_app.backend.services import auth_service

# --- Global state (simple version for now) ---
current_logged_in_user = None

def console_test_authentication(username, password):
    global current_logged_in_user
    print(f"\nAttempting to authenticate user: {username}")
    user_info = auth_service.authenticate_user(username, password)

    if user_info:
        current_logged_in_user = user_info
        print(f"Authentication successful for {username}.")
        print(f"User Info: {user_info}")

        role_name = "Unknown Role"
        try:
            conn = auth_service.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT role_name FROM Roles WHERE id = ?", (user_info['role_id'],))
            role_row = cursor.fetchone()
            if role_row:
                role_name = role_row['role_name']
            conn.close()
        except Exception as e:
            print(f"Error fetching role name: {e}")
        print(f"User Role: {role_name}")

        permissions = auth_service.get_user_permissions(user_info['user_id'])
        print(f"Permissions for {username}: {permissions}")

        # Test specific permissions
        test_perms = ['manage_users', 'submit_leave_request', 'view_reports', 'approve_leave_request']
        for p_name in test_perms:
            if auth_service.user_has_permission(user_info['user_id'], p_name):
                print(f"  - Has permission: '{p_name}'")
            else:
                print(f"  - Does NOT have permission: '{p_name}'")
        current_logged_in_user = None # Reset for next test
    else:
        print(f"Authentication failed for {username}.")


if __name__ == "__main__":
    print("Starting Dawami Application - Console Test Mode")

    # Ensure database and seed data are ready
    db_path = os.path.join(PROJECT_ROOT, "dawami_app", "database", "dawami_dev.db")
    if not os.path.exists(db_path):
        print("Database not found. Please run 'scripts/database_setup.py' and 'scripts/seed_data.py' first.")
        print("Attempting to run setup and seed scripts...")
        try:
            import subprocess
            # Try to determine the correct python executable for venv
            venv_python_candidates = [
                os.path.join(PROJECT_ROOT, "venv", "bin", "python"),
                os.path.join(PROJECT_ROOT, "venv", "bin", "python3"),
                sys.executable # Fallback to current interpreter
            ]
            venv_python = next((p for p in venv_python_candidates if os.path.exists(p)), sys.executable)
            
            print(f"Using Python interpreter: {venv_python} for setup/seed.")

            subprocess.run([venv_python, os.path.join(PROJECT_ROOT, "scripts", "database_setup.py")], check=True, cwd=PROJECT_ROOT)
            subprocess.run([venv_python, os.path.join(PROJECT_ROOT, "scripts", "seed_data.py")], check=True, cwd=PROJECT_ROOT)
            print("Database setup and seeding scripts executed successfully.")
        except Exception as e:
            print(f"Error running setup/seed scripts: {e}. Please run them manually.")
            sys.exit(1)
            
    # Test authentications
    console_test_authentication("admin", "adminpassword")
    console_test_authentication("manager1", "managerpassword")
    console_test_authentication("employee1", "employeepassword")
    console_test_authentication("admin", "wrongpassword")
    console_test_authentication("nonexistentuser", "password")

    print("\nDawami Application Console Test Completed.")
