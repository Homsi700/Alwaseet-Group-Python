import os
import sys
import sqlite3

# Add project root to sys.path to allow importing services and views
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import employee_service
from dawami_app.frontend.views import employee_view # Placeholder UI handlers

DB_DIR = os.path.join(PROJECT_ROOT, "dawami_app", "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

def clear_employees_table():
    """Utility function to clear the Employees table for a clean test run."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Employees")
        conn.commit()
        print("Employees table cleared for testing.")
    except sqlite3.Error as e:
        print(f"Error clearing Employees table: {e}")
    finally:
        if conn:
            conn.close()

def setup_database():
    """Ensures the database and tables exist. Runs setup scripts if DB not found."""
    if not os.path.exists(DB_FILE):
        print(f"Database not found at {DB_FILE}. Running setup scripts...")
        try:
            import subprocess
            venv_python_candidates = [
                os.path.join(PROJECT_ROOT, "venv", "bin", "python"),
                os.path.join(PROJECT_ROOT, "venv", "bin", "python3"),
                sys.executable 
            ]
            venv_python = next((p for p in venv_python_candidates if os.path.exists(p)), sys.executable)
            
            print(f"Using Python interpreter: {venv_python} for setup.")
            subprocess.run([venv_python, os.path.join(PROJECT_ROOT, "scripts", "database_setup.py")], check=True, cwd=PROJECT_ROOT)
            # Seeding is not strictly necessary for employee module tests if we clear the table,
            # but running it ensures all tables (like WorkSchedules) are present.
            subprocess.run([venv_python, os.path.join(PROJECT_ROOT, "scripts", "seed_data.py")], check=True, cwd=PROJECT_ROOT)
            print("Database setup and seeding scripts executed.")
        except Exception as e:
            print(f"Error running setup/seed scripts: {e}. Please ensure they are runnable.")
            sys.exit(1)
    else:
        print(f"Database file found at {DB_FILE}.")
    
    # Add a dummy WorkSchedule if none exists, as employee_service doesn't create them
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM WorkSchedules WHERE schedule_name = 'Default Test Schedule'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO WorkSchedules (schedule_name, expected_start_time, expected_end_time, grace_period_minutes) VALUES (?, ?, ?, ?)",
                           ('Default Test Schedule', '09:00', '17:00', 15))
            conn.commit()
            print("Added 'Default Test Schedule' to WorkSchedules.")
    except sqlite3.Error as e:
        print(f"Error adding default work schedule: {e}")
    finally:
        if conn:
            conn.close()


def main_test_flow():
    print("--- Starting Employee Module Test ---")

    setup_database()
    clear_employees_table() # Start with a clean slate for employee data

    # --- Test employee_service.py directly ---
    print("\n*** Testing employee_service.py directly ***")

    # 1. Add employees
    print("\n1. Adding Employees (Service):")
    emp1_data_service = {
        'first_name': "ServiceTest", 'last_name': "UserOne", 'employee_code': "STU001",
        'department': "Service Dept", 'email': "stu001@example.com",
        'phone_number': "123-001", 'job_title': "Service Tester 1"
    }
    emp1_service = employee_service.add_employee(**emp1_data_service)
    assert emp1_service is not None and emp1_service['employee_code'] == "STU001"

    emp2_data_service = {
        'first_name': "ServiceTest", 'last_name': "UserTwo", 'employee_code': "STU002",
        'department': "Service Dept", 'email': "stu002@example.com",
        'phone_number': "123-002", 'job_title': "Service Tester 2"
    }
    emp2_service = employee_service.add_employee(**emp2_data_service)
    assert emp2_service is not None and emp2_service['employee_code'] == "STU002"
    
    emp3_data_service = { # For deletion test
        'first_name': "ToDelete", 'last_name': "ServiceUser", 'employee_code': "STU003",
        'department': "Temporary", 'email': "stu003@example.com",
        'phone_number': "123-003", 'job_title': "Temporary Tester"
    }
    emp3_service = employee_service.add_employee(**emp3_data_service)
    assert emp3_service is not None and emp3_service['employee_code'] == "STU003"

    # 2. Get a specific employee
    print("\n2. Getting a specific employee (Service):")
    retrieved_emp1 = employee_service.get_employee(emp1_service['id'])
    assert retrieved_emp1 is not None and retrieved_emp1['employee_code'] == "STU001"
    print(f"Retrieved: {retrieved_emp1['first_name']} {retrieved_emp1['last_name']}")

    # 3. Get all employees
    print("\n3. Getting all employees (Service):")
    all_employees_service = employee_service.get_all_employees()
    assert len(all_employees_service) == 3
    print(f"Found {len(all_employees_service)} employees via service.")
    # for emp in all_employees_service: print(f"  - {emp['first_name']} {emp['employee_code']}")


    # 4. Update an employee
    print("\n4. Updating an employee (Service):")
    update_data_service = {'department': "Senior Service Dept", 'job_title': "Lead Service Tester"}
    update_success_service = employee_service.update_employee(emp1_service['id'], **update_data_service)
    assert update_success_service is True
    updated_emp1_service = employee_service.get_employee(emp1_service['id'])
    assert updated_emp1_service['department'] == "Senior Service Dept"
    assert updated_emp1_service['job_title'] == "Lead Service Tester"
    print(f"Updated {updated_emp1_service['first_name']}'s department to: {updated_emp1_service['department']}")

    # 5. Delete an employee
    print("\n5. Deleting an employee (Service):")
    delete_success_service = employee_service.delete_employee(emp3_service['id'])
    assert delete_success_service is True
    deleted_emp3_check_service = employee_service.get_employee(emp3_service['id'])
    assert deleted_emp3_check_service is None
    all_employees_after_delete_service = employee_service.get_all_employees()
    assert len(all_employees_after_delete_service) == 2
    print(f"Employee {emp3_service['employee_code']} deleted. Remaining: {len(all_employees_after_delete_service)}")

    print("\n*** Direct service tests completed successfully. ***")

    # --- Test placeholder UI functions from employee_view.py ---
    print("\n\n*** Testing placeholder UI functions from employee_view.py ***")
    clear_employees_table() # Clean again for UI handler tests

    # 1. Add employees via UI handler
    print("\n1. Adding Employees (UI Handler):")
    emp_ui_data1 = {
        'first_name': "UITest", 'last_name': "UserOne", 'employee_code': "UIU001",
        'department': "UI Dept", 'email': "uiu001@example.com",
        'phone_number': "456-001", 'job_title': "UI Tester 1"
    }
    added_emp_ui1 = employee_view.handle_add_employee_click(emp_ui_data1)
    assert added_emp_ui1 is not None and added_emp_ui1['employee_code'] == "UIU001"
    
    emp_ui_data2 = {
        'first_name': "UITest", 'last_name': "UserTwo", 'employee_code': "UIU002",
        'department': "UI Dept", 'email': "uiu002@example.com",
        'phone_number': "456-002", 'job_title': "UI Tester 2"
    }
    added_emp_ui2 = employee_view.handle_add_employee_click(emp_ui_data2)
    assert added_emp_ui2 is not None and added_emp_ui2['employee_code'] == "UIU002"

    # 2. List employees via UI handler
    employee_view.handle_list_employees_click()

    # 3. View one employee via UI handler
    if added_emp_ui1:
        employee_view.handle_view_employee_click(added_emp_ui1['id'])

    # 4. Update an employee via UI handler
    if added_emp_ui1:
        update_data_ui = {'phone_number': "456-999", 'job_title': "Senior UI Tester"}
        employee_view.handle_update_employee_click(added_emp_ui1['id'], update_data_ui)
        # Verify with service call
        updated_emp_ui1_check = employee_service.get_employee(added_emp_ui1['id'])
        assert updated_emp_ui1_check['phone_number'] == "456-999"

    # 5. Delete an employee via UI handler
    if added_emp_ui2:
        employee_view.handle_delete_employee_click(added_emp_ui2['id'])
        # Verify with service call
        deleted_emp_ui2_check = employee_service.get_employee(added_emp_ui2['id'])
        assert deleted_emp_ui2_check is None
    
    # 6. List employees again
    employee_view.handle_list_employees_click()
    
    # Clean up remaining test employee
    if added_emp_ui1:
        employee_service.delete_employee(added_emp_ui1['id'])

    print("\n*** Placeholder UI function tests completed. ***")
    print("\n--- Employee Module Test Completed Successfully ---")

if __name__ == "__main__":
    main_test_flow()
