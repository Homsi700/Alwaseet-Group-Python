import os
import sys
from datetime import datetime # For testing date range inputs

# Add project root to sys.path to allow importing services
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import attendance_service

# These functions simulate what would be called by actual UI event handlers.

def handle_clock_in_click(employee_id, notes=None):
    """
    Simulates clicking a 'Clock In' button.
    :param employee_id: ID of the employee clocking in.
    :param notes: Optional notes for the clock-in.
    """
    print(f"\n--- Handling Clock In Click (Employee ID: {employee_id}) ---")
    # In a real UI, clock_in_time might be passed if backdating is allowed,
    # otherwise, the service defaults to now().
    log_id = attendance_service.clock_in(employee_id, notes=notes, source='manual_ui')
    if log_id:
        print(f"UI: Employee {employee_id} clocked in. Log ID: {log_id}")
    else:
        print(f"UI: Clock-in failed for employee {employee_id}.")
    return log_id

def handle_clock_out_click(employee_id, notes=None):
    """
    Simulates clicking a 'Clock Out' button.
    :param employee_id: ID of the employee clocking out.
    :param notes: Optional notes for the clock-out.
    """
    print(f"\n--- Handling Clock Out Click (Employee ID: {employee_id}) ---")
    success = attendance_service.clock_out(employee_id, notes=notes)
    if success:
        print(f"UI: Employee {employee_id} clocked out successfully.")
    else:
        print(f"UI: Clock-out failed for employee {employee_id} (perhaps not clocked in or already clocked out).")
    return success

def handle_view_attendance_click(employee_id=None, start_date_str=None, end_date_str=None):
    """
    Simulates viewing attendance records.
    :param employee_id: Optional employee ID to filter by.
    :param start_date_str: Optional start date string (YYYY-MM-DD).
    :param end_date_str: Optional end date string (YYYY-MM-DD).
    """
    print(f"\n--- Handling View Attendance Click ---")
    print(f"UI Params: Employee ID: {employee_id}, Start: {start_date_str}, End: {end_date_str}")

    start_date_obj = None
    end_date_obj = None
    try:
        if start_date_str:
            start_date_obj = datetime.strptime(start_date_str, attendance_service.DATE_FORMAT).date()
        if end_date_str:
            end_date_obj = datetime.strptime(end_date_str, attendance_service.DATE_FORMAT).date()
    except ValueError as e:
        print(f"UI Error: Invalid date format. Please use YYYY-MM-DD. Error: {e}")
        return []

    records = attendance_service.get_attendance_records(
        employee_id=employee_id,
        start_date_obj=start_date_obj,
        end_date_obj=end_date_obj
    )

    if records:
        print(f"UI: Found {len(records)} attendance records:")
        for rec in records:
            print(f"  - EmpID: {rec['employee_id']}, Date: {rec['attendance_date']}, "
                  f"In: {rec['clock_in_time']}, Out: {rec['clock_out_time']}, Notes: {rec['notes']}")
    elif not records and records is not None: # Empty list, not error
        print("UI: No attendance records found matching the criteria.")
    else: # None was returned, indicating a service layer error
        print("UI: Error retrieving attendance records.")
    return records

def handle_get_current_status_click(employee_id):
    """Simulates checking if an employee is currently clocked in."""
    print(f"\n--- Handling Get Current Status Click (Employee ID: {employee_id}) ---")
    open_record = attendance_service.get_open_attendance(employee_id)
    if open_record:
        print(f"UI: Employee {employee_id} is currently CLOCKED IN since {open_record['clock_in_time']}.")
    else:
        print(f"UI: Employee {employee_id} is currently CLOCKED OUT or status unknown.")
    return open_record


if __name__ == '__main__':
    print("Attendance View Module - Placeholder UI Handlers (Direct Demonstration)")

    # Pre-requisite: Ensure database exists and is ideally seeded with employees.
    db_file = os.path.join(PROJECT_ROOT, "dawami_app", "database", "dawami_dev.db")
    if not os.path.exists(db_file):
        print(f"WARNING: Database file not found at {db_file}. Tests might fail or create an empty DB.")
        print("Please run 'scripts/database_setup.py' and 'scripts/seed_data.py' first.")
        sys.exit(1)

    # --- You would need an employee_id from your Employees table to test ---
    # Assuming employee with ID 1 and 2 exist from previous seeding/testing
    TEST_EMP_ID_1 = 1 
    TEST_EMP_ID_2 = 2 

    # Check if test employee 1 exists (rough check)
    from dawami_app.backend.services import employee_service as emp_service # For quick check
    if not emp_service.get_employee(TEST_EMP_ID_1):
         print(f"WARNING: Test Employee ID {TEST_EMP_ID_1} not found. Demo may not be accurate.")
         # Optionally create a dummy employee for demo purposes here if needed
    if not emp_service.get_employee(TEST_EMP_ID_2):
         print(f"WARNING: Test Employee ID {TEST_EMP_ID_2} not found. Demo may not be accurate.")


    print("\nSimulating UI interactions for Attendance...")

    # 1. Employee 1 clocks in
    handle_clock_in_click(TEST_EMP_ID_1, notes="Morning shift start")
    handle_get_current_status_click(TEST_EMP_ID_1)

    # 2. Employee 2 clocks in
    handle_clock_in_click(TEST_EMP_ID_2, notes="Afternoon shift")

    # 3. Employee 1 clocks out
    handle_clock_out_click(TEST_EMP_ID_1, notes="Morning shift end")
    handle_get_current_status_click(TEST_EMP_ID_1)

    # 4. View today's attendance for Employee 1
    today_str = datetime.now().strftime(attendance_service.DATE_FORMAT)
    handle_view_attendance_click(employee_id=TEST_EMP_ID_1, start_date_str=today_str, end_date_str=today_str)
    
    # 5. View all attendance for today
    handle_view_attendance_click(start_date_str=today_str, end_date_str=today_str)

    # 6. Employee 2 clocks out (maybe much later, or next day for realism if tests were multi-day)
    # For demo, just clocking out now.
    handle_clock_out_click(TEST_EMP_ID_2, notes="Afternoon shift end")

    # 7. Try clocking out Employee 1 again (should fail)
    handle_clock_out_click(TEST_EMP_ID_1, notes="Trying to double clock out")
    
    print("\nAttendance View Module Demonstration Complete.")
