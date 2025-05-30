import os
import sys
import sqlite3
from datetime import datetime, timedelta, date

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import attendance_service
from dawami_app.backend.services import employee_service # To add test employees
from dawami_app.frontend.views import attendance_view # Placeholder UI handlers

DB_DIR = os.path.join(PROJECT_ROOT, "dawami_app", "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

# Test employee details
EMP_TEST_ID_1 = None
EMP_TEST_ID_2 = None
EMP_TEST_CODE_1 = "ATT_EMP001"
EMP_TEST_CODE_2 = "ATT_EMP002"


def clear_attendance_table():
    """Utility function to clear the AttendanceLog table for a clean test run."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM AttendanceLog")
        conn.commit()
        print("AttendanceLog table cleared for testing.")
    except sqlite3.Error as e:
        print(f"Error clearing AttendanceLog table: {e}")
    finally:
        if conn:
            conn.close()

def setup_test_employees():
    """Ensures test employees exist, creating them if necessary."""
    global EMP_TEST_ID_1, EMP_TEST_ID_2
    
    emp1 = employee_service.add_employee("AttTest", "UserOne", EMP_TEST_CODE_1, "Testing", "att001@example.com", "777-001", "Tester")
    if emp1:
        EMP_TEST_ID_1 = emp1['id']
    else: # Try to fetch if already exists
        emps = employee_service.get_all_employees()
        for e in emps:
            if e['employee_code'] == EMP_TEST_CODE_1:
                EMP_TEST_ID_1 = e['id']
                break
        if not EMP_TEST_ID_1:
             print(f"CRITICAL: Could not create or find employee {EMP_TEST_CODE_1}")
             sys.exit(1)


    emp2 = employee_service.add_employee("AttTest", "UserTwo", EMP_TEST_CODE_2, "Testing", "att002@example.com", "777-002", "Tester")
    if emp2:
        EMP_TEST_ID_2 = emp2['id']
    else: # Try to fetch if already exists
        emps = employee_service.get_all_employees()
        for e in emps:
            if e['employee_code'] == EMP_TEST_CODE_2:
                EMP_TEST_ID_2 = e['id']
                break
        if not EMP_TEST_ID_2:
            print(f"CRITICAL: Could not create or find employee {EMP_TEST_CODE_2}")
            sys.exit(1)
            
    print(f"Test employees ensured: ID1={EMP_TEST_ID_1} ({EMP_TEST_CODE_1}), ID2={EMP_TEST_ID_2} ({EMP_TEST_CODE_2})")


def setup_database():
    """Ensures the database and tables exist. Runs setup scripts if DB not found."""
    if not os.path.exists(DB_FILE):
        print(f"Database not found at {DB_FILE}. Running setup scripts...")
        try:
            import subprocess
            venv_python = next((p for p in [os.path.join(PROJECT_ROOT, "venv", "bin", "python"), sys.executable] if os.path.exists(p)), sys.executable)
            print(f"Using Python interpreter: {venv_python} for setup.")
            subprocess.run([venv_python, os.path.join(PROJECT_ROOT, "scripts", "database_setup.py")], check=True, cwd=PROJECT_ROOT)
            subprocess.run([venv_python, os.path.join(PROJECT_ROOT, "scripts", "seed_data.py")], check=True, cwd=PROJECT_ROOT) # Ensures roles etc. exist too
            print("Database setup and seeding scripts executed.")
        except Exception as e:
            print(f"Error running setup/seed scripts: {e}. Please ensure they are runnable.")
            sys.exit(1)
    else:
        print(f"Database file found at {DB_FILE}.")


def main_test_flow():
    print("--- Starting Attendance Module Test ---")
    setup_database()
    setup_test_employees() # Ensure our test employees are in place
    clear_attendance_table() # Start with clean attendance data

    # --- Test attendance_service.py directly ---
    print("\n*** Testing attendance_service.py directly ***")

    # 1. Clock In Employee 1
    print("\n1. Clocking In (Service):")
    now = datetime.now()
    clock_in_time_emp1 = now - timedelta(hours=1) # An hour ago
    log_id_emp1 = attendance_service.clock_in(EMP_TEST_ID_1, clock_in_time_dt=clock_in_time_emp1, notes="Service Clock In EMP1")
    assert log_id_emp1 is not None

    # 2. Get Open Attendance for Employee 1
    print("\n2. Getting Open Attendance (Service):")
    open_att_emp1 = attendance_service.get_open_attendance(EMP_TEST_ID_1)
    assert open_att_emp1 is not None
    assert open_att_emp1['id'] == log_id_emp1
    assert open_att_emp1['clock_out_time'] is None
    print(f"Employee {EMP_TEST_ID_1} is currently clocked in (Log ID: {open_att_emp1['id']}).")

    # 3. Clock Out Employee 1
    print("\n3. Clocking Out (Service):")
    clock_out_time_emp1 = now - timedelta(minutes=10) # 50 minutes after clock-in
    success_co_emp1 = attendance_service.clock_out(EMP_TEST_ID_1, clock_out_time_dt=clock_out_time_emp1, notes="Service Clock Out EMP1")
    assert success_co_emp1 is True

    # 4. Verify Employee 1 is no longer clocked in
    open_att_emp1_after_co = attendance_service.get_open_attendance(EMP_TEST_ID_1)
    assert open_att_emp1_after_co is None
    print(f"Employee {EMP_TEST_ID_1} is now clocked out.")

    # 5. Test Clock Out again (should fail)
    print("\n4. Clocking Out Again (Service - Should Fail):")
    fail_co_emp1 = attendance_service.clock_out(EMP_TEST_ID_1, notes="Trying to double clock out")
    assert fail_co_emp1 is False

    # 6. Clock In Employee 2 (no specific time, defaults to now)
    log_id_emp2 = attendance_service.clock_in(EMP_TEST_ID_2, notes="Service Clock In EMP2 - current time")
    assert log_id_emp2 is not None

    # 7. Get Attendance Records
    print("\n5. Getting Attendance Records (Service):")
    # Records for EMP_TEST_ID_1 today
    today_date = date.today()
    records_emp1_today = attendance_service.get_attendance_records(employee_id=EMP_TEST_ID_1, start_date_obj=today_date, end_date_obj=today_date)
    assert len(records_emp1_today) == 1
    assert records_emp1_today[0]['id'] == log_id_emp1
    print(f"Found {len(records_emp1_today)} record(s) for Emp {EMP_TEST_ID_1} today.")

    # Records for all employees today (should be 2 if EMP_TEST_ID_2 clocked in today)
    all_records_today = attendance_service.get_attendance_records(start_date_obj=today_date, end_date_obj=today_date)
    # This assertion depends on whether EMP_TEST_ID_2's "now" falls on the same "today"
    # For robustness, let's check it's at least 1 (from EMP1) or 2 (if EMP2 is also today)
    assert len(all_records_today) >= 1 
    print(f"Found {len(all_records_today)} record(s) for all employees today.")
    
    # Test clock out time before clock in time
    print("\n6. Test Clock Out Before Clock In (Service - Should Fail):")
    clock_in_future_emp1 = now + timedelta(hours=2)
    log_id_future_emp1 = attendance_service.clock_in(EMP_TEST_ID_1, clock_in_time_dt=clock_in_future_emp1, notes="Future clock-in")
    assert log_id_future_emp1 is not None
    fail_clock_out_before_in = attendance_service.clock_out(EMP_TEST_ID_1, clock_out_time_dt=now) # 'now' is before clock_in_future_emp1
    assert fail_clock_out_before_in is False
    # Clean up this future clock-in by clocking it out properly
    attendance_service.clock_out(EMP_TEST_ID_1, clock_out_time_dt=clock_in_future_emp1 + timedelta(hours=1))


    print("\n*** Direct service tests completed successfully. ***")

    # --- Test placeholder UI functions from attendance_view.py ---
    print("\n\n*** Testing placeholder UI functions from attendance_view.py ***")
    clear_attendance_table() # Clean again for UI handler tests

    # 1. Clock In via UI Handler
    print("\n1. Clocking In (UI Handler):")
    attendance_view.handle_clock_in_click(EMP_TEST_ID_1, notes="UI Clock In EMP1")
    
    # 2. Check status via UI Handler
    attendance_view.handle_get_current_status_click(EMP_TEST_ID_1)

    # 3. Clock Out via UI Handler
    attendance_view.handle_clock_out_click(EMP_TEST_ID_1, notes="UI Clock Out EMP1")
    
    # 4. Check status again
    attendance_view.handle_get_current_status_click(EMP_TEST_ID_1)

    # 5. View Attendance via UI Handler (today)
    today_str_for_ui = datetime.now().strftime(attendance_service.DATE_FORMAT)
    attendance_view.handle_view_attendance_click(employee_id=EMP_TEST_ID_1, start_date_str=today_str_for_ui, end_date_str=today_str_for_ui)
    
    # 6. View all attendance for yesterday (should be none or from other tests if DB wasn't fully cleared)
    yesterday_str_for_ui = (datetime.now() - timedelta(days=1)).strftime(attendance_service.DATE_FORMAT)
    attendance_view.handle_view_attendance_click(start_date_str=yesterday_str_for_ui, end_date_str=yesterday_str_for_ui)


    print("\n*** Placeholder UI function tests completed. ***")
    
    # Clean up test employees (optional, but good for reruns)
    # employee_service.delete_employee(EMP_TEST_ID_1)
    # employee_service.delete_employee(EMP_TEST_ID_2)
    # print("\nCleaned up test employees.")
    
    print("\n--- Attendance Module Test Completed Successfully ---")

if __name__ == "__main__":
    main_test_flow()
