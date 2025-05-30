import sqlite3
import os

# Database path configuration
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

def get_db_connection():
    """Creates and returns a database connection."""
    os.makedirs(DB_DIR, exist_ok=True) # Ensure directory exists
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Access columns by name
    return conn

def add_employee(first_name, last_name, employee_code, department, email, phone_number, job_title, work_schedule_id=None, profile_picture_path=None):
    """Adds a new employee to the Employees table."""
    sql = """
        INSERT INTO Employees (first_name, last_name, employee_code, department, email, phone_number, job_title, work_schedule_id, profile_picture_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (first_name, last_name, employee_code, department, email, phone_number, job_title, work_schedule_id, profile_picture_path))
        conn.commit()
        employee_id = cursor.lastrowid
        print(f"Employee '{first_name} {last_name}' (Code: {employee_code}) added successfully with ID: {employee_id}.")
        return {
            'id': employee_id, 'first_name': first_name, 'last_name': last_name, 
            'employee_code': employee_code, 'email': email, 'department': department, 
            'job_title': job_title, 'phone_number': phone_number, 
            'work_schedule_id': work_schedule_id, 'profile_picture_path': profile_picture_path
        }
    except sqlite3.IntegrityError as e:
        print(f"Error adding employee (Code: {employee_code}): {e}. Likely duplicate employee_code or email.")
        return None
    except sqlite3.Error as e:
        print(f"Database error while adding employee (Code: {employee_code}): {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_employee(employee_id):
    """Retrieves an employee by their ID."""
    sql = "SELECT * FROM Employees WHERE id = ?"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (employee_id,))
        employee_row = cursor.fetchone()
        if employee_row:
            return dict(employee_row)
        else:
            print(f"Employee with ID {employee_id} not found.")
            return None
    except sqlite3.Error as e:
        print(f"Database error while fetching employee ID {employee_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_employees():
    """Retrieves all employees from the Employees table."""
    sql = "SELECT * FROM Employees ORDER BY last_name, first_name"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        employees = [dict(row) for row in cursor.fetchall()]
        return employees
    except sqlite3.Error as e:
        print(f"Database error while fetching all employees: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_employee(employee_id, first_name=None, last_name=None, employee_code=None, department=None, email=None, phone_number=None, job_title=None, work_schedule_id=None, profile_picture_path=None):
    """Updates specified fields for a given employee_id."""
    conn = get_db_connection()
    try:
        # Check if employee exists
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Employees WHERE id = ?", (employee_id,))
        if not cursor.fetchone():
            print(f"Cannot update: Employee with ID {employee_id} not found.")
            return False

        fields_to_update = []
        params = []

        if first_name is not None:
            fields_to_update.append("first_name = ?")
            params.append(first_name)
        if last_name is not None:
            fields_to_update.append("last_name = ?")
            params.append(last_name)
        if employee_code is not None:
            fields_to_update.append("employee_code = ?")
            params.append(employee_code)
        if department is not None:
            fields_to_update.append("department = ?")
            params.append(department)
        if email is not None:
            fields_to_update.append("email = ?")
            params.append(email)
        if phone_number is not None:
            fields_to_update.append("phone_number = ?")
            params.append(phone_number)
        if job_title is not None:
            fields_to_update.append("job_title = ?")
            params.append(job_title)
        
        # Handling work_schedule_id explicitly if it can be set to NULL
        if work_schedule_id is not None: # Allows setting to a new ID or to NULL if passed as None by caller
            fields_to_update.append("work_schedule_id = ?")
            params.append(work_schedule_id)
        
        if profile_picture_path is not None: # Allows setting to new path or to NULL
            fields_to_update.append("profile_picture_path = ?")
            params.append(profile_picture_path)

        if not fields_to_update:
            print("No fields provided for update.")
            return False # Or True, depending on desired behavior for no-op

        sql = f"UPDATE Employees SET {', '.join(fields_to_update)} WHERE id = ?"
        params.append(employee_id)
        
        cursor.execute(sql, tuple(params))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"Employee ID {employee_id} updated successfully.")
            return True
        else:
            # This case should ideally be caught by the initial check,
            # but good for robustness if DB state changes.
            print(f"Employee ID {employee_id} not found or data unchanged.")
            return False
            
    except sqlite3.IntegrityError as e:
        print(f"Error updating employee ID {employee_id}: {e}. Likely duplicate employee_code or email.")
        return False
    except sqlite3.Error as e:
        print(f"Database error while updating employee ID {employee_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_employee(employee_id):
    """Deletes an employee by their ID."""
    # Consider implications: What happens to Users linked to this employee?
    # Current Users table schema: FOREIGN KEY (employee_id) REFERENCES Employees (id) ON DELETE SET NULL
    # So, if an employee is deleted, the corresponding user's employee_id will become NULL.
    
    sql = "DELETE FROM Employees WHERE id = ?"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Employees WHERE id = ?", (employee_id,))
        if not cursor.fetchone():
            print(f"Cannot delete: Employee with ID {employee_id} not found.")
            return False

        cursor.execute(sql, (employee_id,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Employee ID {employee_id} deleted successfully.")
            return True
        else:
            # Should be caught by the check above
            print(f"Employee ID {employee_id} not found during delete.")
            return False 
    except sqlite3.Error as e:
        print(f"Database error while deleting employee ID {employee_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    print("Employee Service Module - Direct Execution (for testing)")

    # Ensure DB and tables exist (run database_setup.py first if needed)
    if not os.path.exists(DB_FILE):
        print(f"Database file not found at {DB_FILE}. Please run scripts/database_setup.py first.")
    else:
        print(f"Database file found at {DB_FILE}.")

        # Test adding an employee
        emp1 = add_employee("John", "Doe", "EMP001", "IT", "john.doe@example.com", "123-456-7890", "Software Engineer")
        if emp1:
            print(f"Added Employee: {emp1}")
            emp1_id = emp1['id']

            # Test getting the employee
            retrieved_emp = get_employee(emp1_id)
            print(f"Retrieved Employee: {retrieved_emp}")

            # Test updating the employee
            update_result = update_employee(emp1_id, phone_number="987-654-3210", department="Senior IT")
            print(f"Update Result: {update_result}")
            retrieved_emp_after_update = get_employee(emp1_id)
            print(f"Retrieved Employee after update: {retrieved_emp_after_update}")
        
        # Test adding another employee
        emp2 = add_employee("Jane", "Smith", "EMP002", "HR", "jane.smith@example.com", "111-222-3333", "HR Manager")
        if emp2:
             print(f"Added Employee: {emp2}")

        # Test getting all employees
        all_emps = get_all_employees()
        print(f"All Employees ({len(all_emps)}):")
        for emp in all_emps:
            print(emp)

        # Test deleting an employee (e.g., emp1)
        if emp1:
            delete_result = delete_employee(emp1['id'])
            print(f"Delete Result for EMP001: {delete_result}")
            retrieved_emp_after_delete = get_employee(emp1['id'])
            print(f"Retrieved Employee after delete (should be None): {retrieved_emp_after_delete}")
        
        # Clean up EMP002 for next test run if needed
        if emp2:
             delete_employee(emp2['id'])

        # Test adding employee with duplicate code
        add_employee("Test", "Duplicate", "EMP00X", "Test", "test.dup@example.com", "000", "Tester")
        add_employee("Test", "Duplicate2", "EMP00X", "Test2", "test.dup2@example.com", "001", "Tester2") # Should fail
