import sqlite3
import os
from datetime import datetime, date

# Database path configuration
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

def get_db_connection():
    """Creates and returns a database connection."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- Leave Types ---
def add_leave_type(type_name, default_balance=None):
    """Adds a new leave type."""
    sql = "INSERT INTO LeaveTypes (type_name, default_balance) VALUES (?, ?)"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (type_name, default_balance))
        conn.commit()
        leave_type_id = cursor.lastrowid
        print(f"Leave type '{type_name}' added successfully with ID: {leave_type_id}.")
        return leave_type_id
    except sqlite3.IntegrityError as e:
        print(f"Error adding leave type '{type_name}': {e}. Likely already exists.")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding leave type '{type_name}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_leave_types():
    """Retrieves all leave types."""
    sql = "SELECT * FROM LeaveTypes ORDER BY type_name"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        leave_types = [dict(row) for row in cursor.fetchall()]
        return leave_types
    except sqlite3.Error as e:
        print(f"Database error fetching leave types: {e}")
        return []
    finally:
        if conn:
            conn.close()

# --- Leave Balances ---
def get_leave_balance(employee_id, leave_type_id, year):
    """Retrieves the leave balance for a given employee, leave type, and year."""
    sql = "SELECT balance FROM LeaveBalances WHERE employee_id = ? AND leave_type_id = ? AND year = ?"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (employee_id, leave_type_id, year))
        row = cursor.fetchone()
        if row:
            return row['balance']
        else:
            # Check default balance from LeaveTypes
            cursor.execute("SELECT default_balance FROM LeaveTypes WHERE id = ?", (leave_type_id,))
            lt_row = cursor.fetchone()
            if lt_row and lt_row['default_balance'] is not None:
                # Create an initial balance record based on default for the year
                # This helps if balances are not explicitly set up first for every employee/year
                print(f"No specific balance for EmpID {employee_id}, LTID {leave_type_id}, Year {year}. Using default: {lt_row['default_balance']}")
                # update_leave_balance(employee_id, leave_type_id, year, lt_row['default_balance'], is_initial_balance=True)
                # For now, let's just return the default, actual creation can be handled by update_leave_balance
                return lt_row['default_balance']
            return 0.0 # Default to 0 if no specific record and no default in type
    except sqlite3.Error as e:
        print(f"Database error fetching leave balance: {e}")
        return 0.0
    finally:
        if conn:
            conn.close()

def update_leave_balance(employee_id, leave_type_id, year, change_amount, is_initial_balance=False):
    """
    Updates (or sets initially) the leave balance for an employee.
    If is_initial_balance is True, change_amount is the new balance.
    Otherwise, change_amount is added to the existing balance.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if a record exists
        cursor.execute("SELECT id, balance FROM LeaveBalances WHERE employee_id = ? AND leave_type_id = ? AND year = ?",
                       (employee_id, leave_type_id, year))
        existing_balance_row = cursor.fetchone()

        new_balance = 0.0
        if existing_balance_row:
            if is_initial_balance:
                new_balance = float(change_amount)
            else:
                new_balance = float(existing_balance_row['balance']) + float(change_amount)
            
            sql_update = "UPDATE LeaveBalances SET balance = ? WHERE id = ?"
            cursor.execute(sql_update, (new_balance, existing_balance_row['id']))
        else: # No existing record, create one
            if is_initial_balance:
                new_balance = float(change_amount)
            else: # If not initial and no record, implies starting from 0 or default
                # Get default from leave type if available
                cursor.execute("SELECT default_balance FROM LeaveTypes WHERE id = ?", (leave_type_id,))
                lt_row = cursor.fetchone()
                base_balance = 0.0
                if lt_row and lt_row['default_balance'] is not None:
                    base_balance = float(lt_row['default_balance'])
                new_balance = base_balance + float(change_amount)

            sql_insert = "INSERT INTO LeaveBalances (employee_id, leave_type_id, year, balance) VALUES (?, ?, ?, ?)"
            cursor.execute(sql_insert, (employee_id, leave_type_id, year, new_balance))
        
        conn.commit()
        print(f"Leave balance updated for EmpID {employee_id}, LTID {leave_type_id}, Year {year}. New balance: {new_balance}")
        return new_balance
    except sqlite3.Error as e:
        print(f"Database error updating leave balance: {e}")
        # Attempt to return current balance if update failed mid-way
        return get_leave_balance(employee_id, leave_type_id, year) 
    finally:
        if conn:
            conn.close()

# --- Leave Requests ---
def apply_for_leave(employee_id, leave_type_id, start_date_str, end_date_str, reason):
    """Applies for leave for an employee."""
    request_date_str = datetime.now().strftime(DATETIME_FORMAT)
    status = 'Pending' # Default status

    # Validate date formats (basic)
    try:
        datetime.strptime(start_date_str, DATE_FORMAT)
        datetime.strptime(end_date_str, DATE_FORMAT)
    except ValueError:
        print("Error: Invalid date format. Use YYYY-MM-DD.")
        return None
        
    # Optional: Check if employee_id and leave_type_id exist
    # Optional: Check for overlapping leave requests

    sql = """
        INSERT INTO LeaveRequests (employee_id, leave_type_id, start_date, end_date, reason, status, request_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (employee_id, leave_type_id, start_date_str, end_date_str, reason, status, request_date_str))
        conn.commit()
        request_id = cursor.lastrowid
        print(f"Leave request submitted successfully for EmpID {employee_id}. Request ID: {request_id}")
        return request_id
    except sqlite3.IntegrityError as e:
        print(f"Error submitting leave request (IntegrityError): {e}. Check Employee/LeaveType ID.")
        return None
    except sqlite3.Error as e:
        print(f"Database error submitting leave request: {e}")
        return None
    finally:
        if conn:
            conn.close()

def _update_leave_request_status(leave_request_id, new_status, approver_id):
    """Helper function to update leave request status and approver."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, status FROM LeaveRequests WHERE id = ?", (leave_request_id,))
        request_row = cursor.fetchone()
        if not request_row:
            print(f"Leave request ID {leave_request_id} not found.")
            return False
        
        # Optional: Prevent re-approving/rejecting an already processed request
        # if request_row['status'] not in ['Pending']:
        #     print(f"Leave request ID {leave_request_id} is already '{request_row['status']}'. Cannot change.")
        #     return False

        sql = "UPDATE LeaveRequests SET status = ?, approver_id = ? WHERE id = ?"
        cursor.execute(sql, (new_status, approver_id, leave_request_id))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Leave request ID {leave_request_id} status updated to '{new_status}' by ApproverID {approver_id}.")
            return True
        else: # Should be caught by initial check
            print(f"Failed to update status for leave request ID {leave_request_id} (no rows affected).")
            return False
            
    except sqlite3.Error as e:
        print(f"Database error updating leave request ID {leave_request_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def approve_leave_request(leave_request_id, approver_id):
    """Approves a leave request."""
    return _update_leave_request_status(leave_request_id, 'Approved', approver_id)

def reject_leave_request(leave_request_id, approver_id):
    """Rejects a leave request."""
    return _update_leave_request_status(leave_request_id, 'Rejected', approver_id)

def get_leave_requests(employee_id=None, status=None):
    """Retrieves leave requests, optionally filtered by employee and/or status."""
    params = []
    sql_clauses = []

    if employee_id is not None:
        sql_clauses.append("lr.employee_id = ?")
        params.append(employee_id)
    if status is not None:
        sql_clauses.append("lr.status = ?")
        params.append(status)

    # Join with Employees and LeaveTypes for more meaningful data
    sql = """
        SELECT lr.*, 
               e.first_name || ' ' || e.last_name as employee_name, e.employee_code,
               lt.type_name as leave_type_name,
               u.username as approver_username
        FROM LeaveRequests lr
        JOIN Employees e ON lr.employee_id = e.id
        JOIN LeaveTypes lt ON lr.leave_type_id = lt.id
        LEFT JOIN Users u ON lr.approver_id = u.id 
    """ # Using LEFT JOIN for approver_id in case it's NULL

    if sql_clauses:
        sql += " WHERE " + " AND ".join(sql_clauses)
    sql += " ORDER BY lr.request_date DESC"

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        requests = [dict(row) for row in cursor.fetchall()]
        return requests
    except sqlite3.Error as e:
        print(f"Database error fetching leave requests: {e}")
        return []
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    print("Leave Service Module - Direct Execution (for testing)")
    if not os.path.exists(DB_FILE):
        print(f"Database file not found at {DB_FILE}. Please run setup scripts first.")
        sys.exit(1)

    # Test Leave Types
    print("\n--- Testing Leave Types ---")
    lt_annual_id = add_leave_type("Annual Leave", 20)
    lt_sick_id = add_leave_type("Sick Leave", 10)
    add_leave_type("Unpaid Leave") # No default balance
    
    leave_types = get_leave_types()
    print(f"Available Leave Types ({len(leave_types)}):")
    for lt in leave_types:
        print(f"  ID: {lt['id']}, Name: {lt['type_name']}, Default Balance: {lt.get('default_balance', 'N/A')}")

    # Test Leave Balances (requires employee_id, assume 1 exists from seed_data.py)
    TEST_EMP_ID = 1 
    current_year = datetime.now().year
    
    print(f"\n--- Testing Leave Balances for Employee ID {TEST_EMP_ID}, Year {current_year} ---")
    if lt_annual_id and lt_sick_id:
        update_leave_balance(TEST_EMP_ID, lt_annual_id, current_year, 15, is_initial_balance=True) # Set initial Annual
        bal_annual = get_leave_balance(TEST_EMP_ID, lt_annual_id, current_year)
        print(f"Annual leave balance after setting to 15: {bal_annual}")
        assert bal_annual == 15.0

        update_leave_balance(TEST_EMP_ID, lt_annual_id, current_year, -5) # Deduct 5 days
        bal_annual_after_deduction = get_leave_balance(TEST_EMP_ID, lt_annual_id, current_year)
        print(f"Annual leave balance after deducting 5: {bal_annual_after_deduction}")
        assert bal_annual_after_deduction == 10.0
        
        # Test balance for type not explicitly set for employee (should use default from type if exists)
        bal_sick_default = get_leave_balance(TEST_EMP_ID, lt_sick_id, current_year)
        print(f"Sick leave balance (should be default 10 or 0 if not set): {bal_sick_default}")
        # This assertion depends on whether get_leave_balance auto-creates from default or just returns default
        # Current implementation returns default without creating, so this could be 10 or 0.
        # Let's update it to ensure a record is there for further tests.
        update_leave_balance(TEST_EMP_ID, lt_sick_id, current_year, 7, is_initial_balance=True)
        bal_sick_updated = get_leave_balance(TEST_EMP_ID, lt_sick_id, current_year)
        assert bal_sick_updated == 7.0
        print(f"Sick leave balance after setting to 7: {bal_sick_updated}")


    # Test Leave Requests (requires an approver_id, assume user 1 (admin) exists)
    TEST_APPROVER_ID = 1 
    print(f"\n--- Testing Leave Requests (EmpID: {TEST_EMP_ID}, ApproverID: {TEST_APPROVER_ID}) ---")
    if lt_annual_id:
        req_id_1 = apply_for_leave(TEST_EMP_ID, lt_annual_id, "2024-07-15", "2024-07-17", "Vacation")
        assert req_id_1 is not None
        
        req_id_2 = apply_for_leave(TEST_EMP_ID, lt_annual_id, "2024-08-01", "2024-08-03", "Another Vacation")
        assert req_id_2 is not None

        if req_id_1:
            approve_leave_request(req_id_1, TEST_APPROVER_ID)
        if req_id_2:
            reject_leave_request(req_id_2, TEST_APPROVER_ID)

        requests_all_pending = get_leave_requests(status='Pending')
        print(f"\nPending requests ({len(requests_all_pending)}):")
        for r in requests_all_pending: print(f"  ReqID: {r['id']}, Emp: {r['employee_name']}, Status: {r['status']}")
        
        requests_emp1_all = get_leave_requests(employee_id=TEST_EMP_ID)
        print(f"\nAll requests for Employee {TEST_EMP_ID} ({len(requests_emp1_all)}):")
        for r in requests_emp1_all:
            print(f"  ReqID: {r['id']}, Type: {r['leave_type_name']}, Status: {r['status']}, Approver: {r.get('approver_username', 'N/A')}")
            if r['id'] == req_id_1: assert r['status'] == 'Approved'
            if r['id'] == req_id_2: assert r['status'] == 'Rejected'
    
    # Clean up test data (optional)
    # conn = get_db_connection()
    # cursor = conn.cursor()
    # if lt_annual_id: cursor.execute("DELETE FROM LeaveTypes WHERE id = ?", (lt_annual_id,))
    # if lt_sick_id: cursor.execute("DELETE FROM LeaveTypes WHERE id = ?", (lt_sick_id,))
    # cursor.execute("DELETE FROM LeaveTypes WHERE type_name = 'Unpaid Leave'")
    # cursor.execute("DELETE FROM LeaveBalances WHERE employee_id = ?", (TEST_EMP_ID,))
    # cursor.execute("DELETE FROM LeaveRequests WHERE employee_id = ?", (TEST_EMP_ID,))
    # conn.commit()
    # conn.close()
    # print("\nCleaned up test leave data.")
