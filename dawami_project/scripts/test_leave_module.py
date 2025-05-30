import os
import sys
import sqlite3
from datetime import datetime, date, timedelta

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import leave_service
from dawami_app.backend.services import employee_service # To ensure test employees
from dawami_app.backend.services import auth_service # To ensure test users (approvers)
from dawami_app.frontend.views import leave_view # Placeholder UI handlers

DB_DIR = os.path.join(PROJECT_ROOT, "dawami_app", "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

# Test Employee and User (Approver) details
TEST_EMP_ID = None
TEST_EMP_CODE = "LEAVE_EMP01"
TEST_APPROVER_USER_ID = None
TEST_APPROVER_USERNAME = "leave_approver"

# Leave Type IDs to be fetched/created during tests
LT_ANNUAL_ID = None
LT_SICK_ID = None
LT_UNPAID_ID = None

def clear_leave_related_tables():
    """Clears tables specific to leave module tests for a clean run."""
    print("\nClearing leave-related tables (LeaveRequests, LeaveBalances, LeaveTypes)...")
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM LeaveRequests")
        cursor.execute("DELETE FROM LeaveBalances")
        # Be cautious with LeaveTypes if they are meant to be more static.
        # For full test isolation, clearing them is okay.
        cursor.execute("DELETE FROM LeaveTypes")
        conn.commit()
        print("LeaveRequests, LeaveBalances, and LeaveTypes tables cleared.")
    except sqlite3.Error as e:
        print(f"Error clearing leave tables: {e}")
    finally:
        if conn:
            conn.close()

def setup_test_entities():
    """Ensures test employees and users (approvers) exist."""
    global TEST_EMP_ID, TEST_APPROVER_USER_ID

    # Ensure Employee
    emp = employee_service.add_employee("LeaveTest", "User", TEST_EMP_CODE, "LeaveDept", 
                                        f"{TEST_EMP_CODE.lower()}@example.com", "888-001", "Leave Tester")
    if emp:
        TEST_EMP_ID = emp['id']
    else:
        emps = employee_service.get_all_employees()
        for e_item in emps:
            if e_item['employee_code'] == TEST_EMP_CODE:
                TEST_EMP_ID = e_item['id']
                break
    if not TEST_EMP_ID:
        print(f"CRITICAL: Could not create or find employee {TEST_EMP_CODE}")
        sys.exit(1)
    print(f"Test Employee ensured: ID={TEST_EMP_ID} (Code: {TEST_EMP_CODE})")

    # Ensure Approver User (linked to an Admin role, not necessarily an employee for this test)
    # auth_service.create_user ensures roles 'Admin', 'Manager', 'Employee' exist.
    approver = auth_service.create_user(TEST_APPROVER_USERNAME, "approvepass", "Manager") # Or Admin
    if approver:
        TEST_APPROVER_USER_ID = approver['id']
    else: # Try to fetch if user already exists
        conn = auth_service.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Users WHERE username = ?", (TEST_APPROVER_USERNAME,))
        user_row = cursor.fetchone()
        if user_row:
            TEST_APPROVER_USER_ID = user_row['id']
        conn.close()
    
    if not TEST_APPROVER_USER_ID:
        print(f"CRITICAL: Could not create or find approver user {TEST_APPROVER_USERNAME}")
        sys.exit(1)
    print(f"Test Approver User ensured: ID={TEST_APPROVER_USER_ID} (Username: {TEST_APPROVER_USERNAME})")


def setup_database_and_base_data():
    """Ensures the DB, tables, and some base data (like roles via seed) exist."""
    if not os.path.exists(DB_FILE):
        print(f"Database not found at {DB_FILE}. Running setup scripts...")
        try:
            import subprocess
            venv_python = next((p for p in [os.path.join(PROJECT_ROOT, "venv", "bin", "python"), sys.executable] if os.path.exists(p)), sys.executable)
            print(f"Using Python interpreter: {venv_python} for setup.")
            subprocess.run([venv_python, os.path.join(PROJECT_ROOT, "scripts", "database_setup.py")], check=True, cwd=PROJECT_ROOT)
            subprocess.run([venv_python, os.path.join(PROJECT_ROOT, "scripts", "seed_data.py")], check=True, cwd=PROJECT_ROOT)
            print("Database setup and seeding scripts executed.")
        except Exception as e:
            print(f"Error running setup/seed scripts: {e}.")
            sys.exit(1)
    else:
        print(f"Database file found at {DB_FILE}.")
    
    setup_test_entities() # Create specific employees/users for this test module


def calculate_leave_duration(start_date_str, end_date_str):
    """Calculates duration of leave in days, inclusive."""
    try:
        start_date = datetime.strptime(start_date_str, leave_service.DATE_FORMAT).date()
        end_date = datetime.strptime(end_date_str, leave_service.DATE_FORMAT).date()
        return (end_date - start_date).days + 1
    except ValueError:
        return 0


def main_test_flow():
    print("--- Starting Leave Module Test ---")
    setup_database_and_base_data()
    clear_leave_related_tables() # Clean specific tables for these tests

    current_year = datetime.now().year
    global LT_ANNUAL_ID, LT_SICK_ID, LT_UNPAID_ID

    # --- Test leave_service.py directly ---
    print("\n*** Testing leave_service.py directly ***")

    # 1. Add Leave Types
    print("\n1. Adding Leave Types (Service):")
    LT_ANNUAL_ID = leave_service.add_leave_type("Annual Test Leave", 20)
    assert LT_ANNUAL_ID is not None
    LT_SICK_ID = leave_service.add_leave_type("Sick Test Leave", 10)
    assert LT_SICK_ID is not None
    LT_UNPAID_ID = leave_service.add_leave_type("Unpaid Test Leave") # No default balance
    assert LT_UNPAID_ID is not None
    
    leave_types_service = leave_service.get_leave_types()
    assert len(leave_types_service) >= 3 # Could be more if DB wasn't perfectly clean before
    print(f"Found {len(leave_types_service)} leave types via service.")

    # 2. Set Initial Leave Balances
    print("\n2. Setting Initial Leave Balances (Service):")
    bal_annual_set = leave_service.update_leave_balance(TEST_EMP_ID, LT_ANNUAL_ID, current_year, 20, is_initial_balance=True)
    assert bal_annual_set == 20.0
    bal_sick_set = leave_service.update_leave_balance(TEST_EMP_ID, LT_SICK_ID, current_year, 10, is_initial_balance=True)
    assert bal_sick_set == 10.0
    bal_unpaid_set = leave_service.update_leave_balance(TEST_EMP_ID, LT_UNPAID_ID, current_year, 0, is_initial_balance=True)
    assert bal_unpaid_set == 0.0

    # 3. Get Balances to verify
    assert leave_service.get_leave_balance(TEST_EMP_ID, LT_ANNUAL_ID, current_year) == 20.0
    assert leave_service.get_leave_balance(TEST_EMP_ID, LT_SICK_ID, current_year) == 10.0
    print("Initial balances verified.")

    # 4. Apply for Leave
    print("\n3. Applying for Leave (Service):")
    req1_start_str = (date.today() + timedelta(days=30)).strftime(leave_service.DATE_FORMAT)
    req1_end_str = (date.today() + timedelta(days=34)).strftime(leave_service.DATE_FORMAT) # 5 days
    req1_id = leave_service.apply_for_leave(TEST_EMP_ID, LT_ANNUAL_ID, req1_start_str, req1_end_str, "Annual holiday")
    assert req1_id is not None

    req2_start_str = (date.today() + timedelta(days=60)).strftime(leave_service.DATE_FORMAT)
    req2_end_str = (date.today() + timedelta(days=61)).strftime(leave_service.DATE_FORMAT) # 2 days
    req2_id = leave_service.apply_for_leave(TEST_EMP_ID, LT_SICK_ID, req2_start_str, req2_end_str, "Medical checkup")
    assert req2_id is not None
    
    req3_start_str = (date.today() + timedelta(days=90)).strftime(leave_service.DATE_FORMAT)
    req3_end_str = (date.today() + timedelta(days=90)).strftime(leave_service.DATE_FORMAT) # 1 day
    req3_id = leave_service.apply_for_leave(TEST_EMP_ID, LT_UNPAID_ID, req3_start_str, req3_end_str, "Personal day")
    assert req3_id is not None


    # 5. Approve one request, Reject another
    print("\n4. Approving/Rejecting Leave (Service):")
    assert leave_service.approve_leave_request(req1_id, TEST_APPROVER_USER_ID) is True
    assert leave_service.reject_leave_request(req2_id, TEST_APPROVER_USER_ID) is True
    # req3 remains Pending

    # 6. Check Statuses
    requests_after_action = leave_service.get_leave_requests(employee_id=TEST_EMP_ID)
    found_req1, found_req2, found_req3 = False, False, False
    for r in requests_after_action:
        if r['id'] == req1_id: assert r['status'] == 'Approved'; found_req1 = True
        if r['id'] == req2_id: assert r['status'] == 'Rejected'; found_req2 = True
        if r['id'] == req3_id: assert r['status'] == 'Pending'; found_req3 = True
    assert found_req1 and found_req2 and found_req3
    print("Leave request statuses verified.")

    # 7. Simulate Leave Balance Deduction for Approved Leave
    print("\n5. Simulating Balance Deduction for Approved Leave (Service):")
    approved_leave_duration = calculate_leave_duration(req1_start_str, req1_end_str) # Should be 5
    assert approved_leave_duration == 5
    
    # Deduct from balance
    bal_annual_after_deduction = leave_service.update_leave_balance(TEST_EMP_ID, LT_ANNUAL_ID, current_year, -approved_leave_duration)
    assert bal_annual_after_deduction == (20.0 - approved_leave_duration) # 20 - 5 = 15
    print(f"Annual leave balance is now {bal_annual_after_deduction} after approved leave deduction.")

    # Balance for sick leave should be unchanged as it was rejected
    assert leave_service.get_leave_balance(TEST_EMP_ID, LT_SICK_ID, current_year) == 10.0
    print("Sick leave balance remains unchanged for rejected request.")

    print("\n*** Direct service tests completed successfully. ***")

    # --- Test placeholder UI functions from leave_view.py ---
    print("\n\n*** Testing placeholder UI functions from leave_view.py ***")
    clear_leave_related_tables() # Clean again for UI handler tests
    
    # Re-add leave types via UI handlers
    lt_annual_ui_id = leave_view.handle_add_leave_type_click("Annual UI Leave", 25)
    lt_sick_ui_id = leave_view.handle_add_leave_type_click("Sick UI Leave", 15)
    assert lt_annual_ui_id is not None and lt_sick_ui_id is not None
    leave_view.handle_get_leave_types_click()

    # Set initial balances via UI
    leave_view.handle_update_leave_balance_click(TEST_EMP_ID, lt_annual_ui_id, current_year, 25, is_initial_balance=True)
    leave_view.handle_view_leave_balance_click(TEST_EMP_ID, lt_annual_ui_id, current_year)

    # Apply for leave via UI
    ui_req_start = (date.today() + timedelta(days=10)).strftime(leave_service.DATE_FORMAT)
    ui_req_end = (date.today() + timedelta(days=12)).strftime(leave_service.DATE_FORMAT) # 3 days
    ui_req_id = leave_view.handle_apply_leave_click(TEST_EMP_ID, lt_annual_ui_id, ui_req_start, ui_req_end, "UI Test Vacation")
    assert ui_req_id is not None

    # View pending requests via UI
    leave_view.handle_view_leave_requests_click(status='Pending')

    # Approve request via UI
    leave_view.handle_approve_leave_click(ui_req_id, TEST_APPROVER_USER_ID)
    
    # Check status via UI
    leave_view.handle_view_leave_requests_click(employee_id=TEST_EMP_ID, status='Approved')

    # Deduct balance via UI (simulating post-approval process)
    ui_leave_duration = calculate_leave_duration(ui_req_start, ui_req_end) # 3 days
    leave_view.handle_update_leave_balance_click(TEST_EMP_ID, lt_annual_ui_id, current_year, -ui_leave_duration)
    leave_view.handle_view_leave_balance_click(TEST_EMP_ID, lt_annual_ui_id, current_year) # Should be 25 - 3 = 22


    print("\n*** Placeholder UI function tests completed. ***")
    print("\n--- Leave Module Test Completed Successfully ---")

if __name__ == "__main__":
    main_test_flow()
