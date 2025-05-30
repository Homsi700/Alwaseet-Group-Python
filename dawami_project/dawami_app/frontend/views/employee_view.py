import os
import sys

# Add project root to sys.path to allow importing services
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import employee_service

# These functions simulate what would be called by actual UI event handlers.
# Due to previous tkinter issues, we are not building the actual UI here,
# but these functions provide the hooks for future UI integration and for testing the service calls.

def handle_add_employee_click(employee_data):
    """
    Simulates clicking an 'Add Employee' button after filling a form.
    :param employee_data: A dictionary with employee details.
                          Example: {'first_name': "Jane", 'last_name': "Doe", ...}
    """
    print("\n--- Handling Add Employee Click ---")
    if not all(k in employee_data for k in ['first_name', 'last_name', 'employee_code', 'department', 'email', 'phone_number', 'job_title']):
        print("Error: Missing required employee data fields.")
        return None
    
    new_employee = employee_service.add_employee(
        first_name=employee_data['first_name'],
        last_name=employee_data['last_name'],
        employee_code=employee_data['employee_code'],
        department=employee_data['department'],
        email=employee_data['email'],
        phone_number=employee_data['phone_number'],
        job_title=employee_data['job_title'],
        work_schedule_id=employee_data.get('work_schedule_id'), # Optional
        profile_picture_path=employee_data.get('profile_picture_path') # Optional
    )
    if new_employee:
        print(f"UI: Employee added successfully. Details: {new_employee}")
    else:
        print("UI: Failed to add employee.")
    return new_employee

def handle_view_employee_click(employee_id):
    """Simulates viewing details of a specific employee."""
    print(f"\n--- Handling View Employee Click (ID: {employee_id}) ---")
    employee = employee_service.get_employee(employee_id)
    if employee:
        print(f"UI: Employee details: {employee}")
    else:
        print(f"UI: Employee with ID {employee_id} not found.")
    return employee

def handle_list_employees_click():
    """Simulates listing all employees."""
    print("\n--- Handling List Employees Click ---")
    employees = employee_service.get_all_employees()
    if employees:
        print(f"UI: Found {len(employees)} employees:")
        for emp in employees:
            print(f"  - {emp['first_name']} {emp['last_name']} ({emp['employee_code']})")
    else:
        print("UI: No employees found or an error occurred.")
    return employees

def handle_update_employee_click(employee_id, data_to_update):
    """
    Simulates updating an existing employee's details.
    :param employee_id: ID of the employee to update.
    :param data_to_update: A dictionary with fields to update.
                           Example: {'phone_number': "555-1234", 'job_title': "Senior Developer"}
    """
    print(f"\n--- Handling Update Employee Click (ID: {employee_id}) ---")
    print(f"UI: Attempting to update employee ID {employee_id} with data: {data_to_update}")
    success = employee_service.update_employee(employee_id, **data_to_update)
    if success:
        print(f"UI: Employee ID {employee_id} updated successfully.")
        # Optionally, fetch and display the updated employee
        updated_employee = employee_service.get_employee(employee_id)
        print(f"UI: Updated details: {updated_employee}")
    else:
        print(f"UI: Failed to update employee ID {employee_id}.")
    return success

def handle_delete_employee_click(employee_id):
    """Simulates deleting an employee."""
    print(f"\n--- Handling Delete Employee Click (ID: {employee_id}) ---")
    success = employee_service.delete_employee(employee_id)
    if success:
        print(f"UI: Employee ID {employee_id} deleted successfully.")
    else:
        print(f"UI: Failed to delete employee ID {employee_id}.")
    return success

if __name__ == '__main__':
    # This section is for demonstrating how these handlers would be used.
    # Actual testing of services will be done in test_employee_module.py
    print("Employee View Module - Placeholder UI Handlers (Direct Demonstration)")

    # Pre-requisite: Ensure database exists and is ideally seeded or clean.
    # For this direct demo, we assume the DB exists.
    # Running database_setup.py is a good first step.
    
    db_file = os.path.join(PROJECT_ROOT, "dawami_app", "database", "dawami_dev.db")
    if not os.path.exists(db_file):
        print(f"WARNING: Database file not found at {db_file}. Tests might fail or create an empty DB.")
        print("Please run 'scripts/database_setup.py' first.")

    print("\nSimulating some UI interactions...")

    # 1. Add a new employee
    sample_emp_data_1 = {
        'first_name': "Alice", 'last_name': "Wonderland", 'employee_code': "EMP010",
        'department': "Curiosity", 'email': "alice.w@example.com",
        'phone_number': "111- wonderland", 'job_title': "Explorer"
    }
    added_emp_1 = handle_add_employee_click(sample_emp_data_1)
    
    # 2. Add another employee
    sample_emp_data_2 = {
        'first_name': "Bob", 'last_name': "The Builder", 'employee_code': "EMP011",
        'department': "Construction", 'email': "bob.b@example.com",
        'phone_number': "222-buildit", 'job_title': "Master Builder"
    }
    added_emp_2 = handle_add_employee_click(sample_emp_data_2)

    # 3. List all employees
    handle_list_employees_click()

    # 4. View one employee (if added)
    if added_emp_1:
        handle_view_employee_click(added_emp_1['id'])

    # 5. Update an employee (if added)
    if added_emp_1:
        update_data = {'phone_number': "111-rabbit-hole", 'job_title': "Chief Explorer"}
        handle_update_employee_click(added_emp_1['id'], update_data)

    # 6. Delete an employee (if added)
    if added_emp_2:
        handle_delete_employee_click(added_emp_2['id'])
    
    # 7. List employees again to see changes
    handle_list_employees_click()

    # Clean up the first test employee if it was created
    if added_emp_1:
        print(f"\nDemo cleanup: Deleting employee ID {added_emp_1['id']}")
        employee_service.delete_employee(added_emp_1['id'])

    print("\nEmployee View Module Demonstration Complete.")
