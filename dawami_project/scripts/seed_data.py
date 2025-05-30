import sqlite3
import os
import sys

# Add the project root to the Python path to allow importing auth_service
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import auth_service

DB_DIR = os.path.join(PROJECT_ROOT, "dawami_app", "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

def get_db_connection():
    """Creates and returns a database connection."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def seed_roles_and_permissions():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # --- Seed Roles (Idempotent) ---
        roles = [
            ('Admin', 'Administrator with full system access.'),
            ('Manager', 'Manager with supervisory privileges.'),
            ('Employee', 'Regular employee with standard access.')
        ]
        role_ids = {}
        for name, desc in roles:
            cursor.execute("SELECT id FROM Roles WHERE role_name = ?", (name,))
            role_row = cursor.fetchone()
            if role_row:
                role_ids[name] = role_row['id']
                print(f"Role '{name}' already exists with ID: {role_ids[name]}.")
            else:
                cursor.execute("INSERT INTO Roles (role_name, description) VALUES (?, ?)", (name, desc))
                role_ids[name] = cursor.lastrowid
                print(f"Role '{name}' created with ID: {role_ids[name]}.")

        # --- Seed Permissions (Idempotent) ---
        permissions = [
            ('manage_users', 'Ability to create, edit, and delete users.'),
            ('view_reports', 'Ability to view system reports.'),
            ('submit_leave_request', 'Ability to submit leave requests.'),
            ('approve_leave_request', 'Ability to approve or reject leave requests.'),
            ('manage_settings', 'Ability to change system settings.'),
            ('record_attendance_manual', 'Ability to manually record attendance.')
            # Add more specific permissions as needed:
            # 'view_own_attendance', 'view_team_attendance', 
            # 'edit_own_profile', 'manage_employee_profiles',
            # 'manage_schedules', 'manage_leave_types'
        ]
        permission_ids = {}
        for name, desc in permissions:
            cursor.execute("SELECT id FROM Permissions WHERE permission_name = ?", (name,))
            perm_row = cursor.fetchone()
            if perm_row:
                permission_ids[name] = perm_row['id']
                print(f"Permission '{name}' already exists with ID: {permission_ids[name]}.")
            else:
                cursor.execute("INSERT INTO Permissions (permission_name, description) VALUES (?, ?)", (name, desc))
                permission_ids[name] = cursor.lastrowid
                print(f"Permission '{name}' created with ID: {permission_ids[name]}.")

        # --- Seed RolePermissions (Idempotent) ---
        # Define which permissions each role gets
        role_permission_map = {
            'Admin': ['manage_users', 'view_reports', 'submit_leave_request', 'approve_leave_request', 'manage_settings', 'record_attendance_manual'],
            'Manager': ['view_reports', 'approve_leave_request', 'record_attendance_manual'],
            'Employee': ['submit_leave_request', 'record_attendance_manual']
        }

        for role_name, perm_names in role_permission_map.items():
            current_role_id = role_ids.get(role_name)
            if not current_role_id:
                print(f"Warning: Role ID for '{role_name}' not found. Skipping permissions.")
                continue
            for perm_name in perm_names:
                current_perm_id = permission_ids.get(perm_name)
                if not current_perm_id:
                    print(f"Warning: Permission ID for '{perm_name}' not found. Skipping for role '{role_name}'.")
                    continue
                
                cursor.execute("SELECT role_id FROM RolePermissions WHERE role_id = ? AND permission_id = ?", (current_role_id, current_perm_id))
                if cursor.fetchone():
                    print(f"Permission '{perm_name}' already assigned to role '{role_name}'.")
                else:
                    cursor.execute("INSERT INTO RolePermissions (role_id, permission_id) VALUES (?, ?)", (current_role_id, current_perm_id))
                    print(f"Assigned permission '{perm_name}' to role '{role_name}'.")
        
        conn.commit()
        print("Roles, Permissions, and RolePermissions seeded successfully.")

    except sqlite3.Error as e:
        print(f"Database error during seeding: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def seed_users():
    # --- Create Default Admin User ---
    # `create_user` already ensures roles exist.
    admin_user = auth_service.create_user("admin", "adminpassword", "Admin")
    if admin_user:
        print(f"Admin user '{admin_user['username']}' created/verified.")
    else:
        print("Failed to create admin user or user already exists with a different configuration.")

    # --- Create Sample Employee and Employee User ---
    # For employee user, we might need a placeholder employee record first.
    # Let's insert a minimal one if it doesn't exist.
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sample_employee_code = "EMP000"
        cursor.execute("SELECT id FROM Employees WHERE employee_code = ?", (sample_employee_code,))
        emp_row = cursor.fetchone()
        employee_id_for_user = None

        if emp_row:
            employee_id_for_user = emp_row['id']
            print(f"Employee with code '{sample_employee_code}' already exists with ID: {employee_id_for_user}.")
        else:
            cursor.execute("""
                INSERT INTO Employees (first_name, last_name, employee_code, email, department, job_title)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Sample", "Employee", sample_employee_code, "employee1@example.com", "General", "Staff"))
            employee_id_for_user = cursor.lastrowid
            conn.commit()
            print(f"Created placeholder employee '{sample_employee_code}' with ID: {employee_id_for_user}.")
        
        if employee_id_for_user:
            emp_user = auth_service.create_user("employee1", "employeepassword", "Employee", employee_id=employee_id_for_user)
            if emp_user:
                print(f"Employee user '{emp_user['username']}' created/verified for employee ID {employee_id_for_user}.")
            else:
                print(f"Failed to create employee user for employee ID {employee_id_for_user} or user already exists.")
        else:
            print("Could not obtain an employee_id for creating a sample employee user.")

    except sqlite3.Error as e:
        print(f"Database error during user seeding (employee part): {e}")
    finally:
        if conn:
            conn.close()
    
    # Create a manager user (without employee_id for now, or create another sample employee)
    manager_user = auth_service.create_user("manager1", "managerpassword", "Manager")
    if manager_user:
        print(f"Manager user '{manager_user['username']}' created/verified.")
    else:
        print("Failed to create manager user or user already exists.")


if __name__ == "__main__":
    print("Starting database seeding process...")
    # 1. Ensure the database and tables are created by running database_setup.py first
    #    (This script assumes tables already exist)
    
    # Check if DB file exists, if not, prompt to run database_setup.py
    if not os.path.exists(DB_FILE):
        print(f"Database file not found at {DB_FILE}.")
        print("Please run 'python scripts/database_setup.py' first to create the database and tables.")
        # Optionally, you could try to run it from here:
        # print("Attempting to run database_setup.py...")
        # import subprocess
        # setup_script_path = os.path.join(PROJECT_ROOT, "scripts", "database_setup.py")
        # try:
        #     subprocess.run([sys.executable, setup_script_path], check=True)
        #     print("database_setup.py executed successfully.")
        # except subprocess.CalledProcessError as e:
        #     print(f"Error running database_setup.py: {e}")
        #     exit(1)
        # except FileNotFoundError:
        #     print(f"Could not find database_setup.py at {setup_script_path}")
        #     exit(1)
    else:
        print(f"Database file found at {DB_FILE}.")

    seed_roles_and_permissions()
    seed_users()
    print("Database seeding process completed.")
