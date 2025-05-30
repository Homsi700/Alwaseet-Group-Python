import os
import sys
import sqlite3
from datetime import datetime, date, timedelta

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import reporting_service
from dawami_app.backend.services import employee_service
from dawami_app.backend.services import attendance_service
from dawami_app.backend.services import leave_service # Import the module
from dawami_app.backend.services import auth_service # For creating approver user
from dawami_app.frontend.views import reporting_view # Placeholder UI handlers

DB_DIR = os.path.join(PROJECT_ROOT, "dawami_app", "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

# Test entity IDs
EMP_RPT_ID_1, EMP_RPT_ID_2, EMP_RPT_ID_3 = None, None, None
EMP_RPT_CODE_1, EMP_RPT_CODE_2, EMP_RPT_CODE_3 = "RPTEMP001", "RPTEMP002", "RPTEMP003"
APPROVER_RPT_ID = None
LT_ANNUAL_RPT_ID, LT_SICK_RPT_ID = None, None

def clear_test_data():
    """Clears data specific to this test module for a cleaner run."""
    print("\nClearing reporting module specific test data...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Delete specific employees if they exist by code
        for code in [EMP_RPT_CODE_1, EMP_RPT_CODE_2, EMP_RPT_CODE_3]:
            cursor.execute("SELECT id FROM Employees WHERE employee_code = ?", (code,))
            emp_row = cursor.fetchone()
            if emp_row:
                emp_id_to_delete = emp_row[0]
                cursor.execute("DELETE FROM AttendanceLog WHERE employee_id = ?", (emp_id_to_delete,))
                cursor.execute("DELETE FROM LeaveRequests WHERE employee_id = ?", (emp_id_to_delete,))
                cursor.execute("DELETE FROM LeaveBalances WHERE employee_id = ?", (emp_id_to_delete,))
                cursor.execute("DELETE FROM Users WHERE employee_id = ?", (emp_id_to_delete,)) # If users are linked
                cursor.execute("DELETE FROM Employees WHERE id = ?", (emp_id_to_delete,))
        
        # Clear specific leave types by name if they exist
        for lt_name in ["Annual Report Test", "Sick Report Test"]:
            cursor.execute("DELETE FROM LeaveTypes WHERE type_name = ?", (lt_name,))
        
        # Clear specific users if they exist
        cursor.execute("DELETE FROM Users WHERE username = 'rpt_approver'")
        conn.commit()
        print("Specific test data cleared (employees, related logs, specific leave types, specific user).")
    except sqlite3.Error as e:
        print(f"Error clearing test data: {e}")
    finally:
        conn.close()

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

def seed_specific_data_for_reports():
    global EMP_RPT_ID_1, EMP_RPT_ID_2, EMP_RPT_ID_3, APPROVER_RPT_ID, LT_ANNUAL_RPT_ID, LT_SICK_RPT_ID
    print("\nSeeding specific data for reporting tests...")

    # Employees
    emp1 = employee_service.add_employee("ReportEmp", "One", EMP_RPT_CODE_1, "ReportsDept", "rpt001@example.com", "999-001", "Analyst")
    EMP_RPT_ID_1 = emp1['id'] if emp1 else employee_service.get_all_employees()[-1]['id'] # Fallback, assumes last added if exists
    emp2 = employee_service.add_employee("ReportEmp", "Two", EMP_RPT_CODE_2, "ReportsDept", "rpt002@example.com", "999-002", "Specialist")
    EMP_RPT_ID_2 = emp2['id'] if emp2 else employee_service.get_all_employees()[-2]['id']
    emp3 = employee_service.add_employee("ReportEmp", "Three", EMP_RPT_CODE_3, "Finance", "rpt003@example.com", "999-003", "Accountant")
    EMP_RPT_ID_3 = emp3['id'] if emp3 else employee_service.get_all_employees()[-3]['id']
    print(f"Test Employees: E1_ID={EMP_RPT_ID_1}, E2_ID={EMP_RPT_ID_2}, E3_ID={EMP_RPT_ID_3}")

    # Approver User (Manager)
    approver_user = auth_service.create_user("rpt_approver", "rptpass", "Manager", employee_id=EMP_RPT_ID_1) # Manager can be an employee
    APPROVER_RPT_ID = approver_user['id'] if approver_user else auth_service.authenticate_user("rpt_approver", "rptpass")['user_id']
    print(f"Test Approver: UserID={APPROVER_RPT_ID}")

    # Leave Types
    LT_ANNUAL_RPT_ID = leave_service.add_leave_type("Annual Report Test", 20)
    LT_SICK_RPT_ID = leave_service.add_leave_type("Sick Report Test", 10)
    print(f"Test Leave Types: AnnualID={LT_ANNUAL_RPT_ID}, SickID={LT_SICK_RPT_ID}")


    # Attendance Data
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Emp1: Present today, worked full day
    att_serv_cin1_dt = datetime.combine(today, datetime.min.time()) + timedelta(hours=9) # Today 9 AM
    att_serv_cout1_dt = datetime.combine(today, datetime.min.time()) + timedelta(hours=17, minutes=30) # Today 5:30 PM
    attendance_service.clock_in(EMP_RPT_ID_1, clock_in_time_dt=att_serv_cin1_dt, source="test_setup")
    attendance_service.clock_out(EMP_RPT_ID_1, clock_out_time_dt=att_serv_cout1_dt, notes="Full day")

    # Emp2: Present today, still clocked IN
    att_serv_cin2_dt = datetime.combine(today, datetime.min.time()) + timedelta(hours=10) # Today 10 AM
    attendance_service.clock_in(EMP_RPT_ID_2, clock_in_time_dt=att_serv_cin2_dt, source="test_setup", notes="Late start")

    # Emp1: Present yesterday also
    att_serv_cin3_dt = datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=8, minutes=45)
    att_serv_cout3_dt = datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=17, minutes=15)
    attendance_service.clock_in(EMP_RPT_ID_1, clock_in_time_dt=att_serv_cin3_dt, source="test_setup")
    attendance_service.clock_out(EMP_RPT_ID_1, clock_out_time_dt=att_serv_cout3_dt, notes="Yesterday's work")
    print("Seeded attendance data.")

    # Leave Data
    # Emp2: Approved annual leave that includes today
    leave_service.apply_for_leave(EMP_RPT_ID_2, LT_ANNUAL_RPT_ID, 
                                  (today - timedelta(days=1)).strftime(leave_service.DATE_FORMAT), 
                                  (today + timedelta(days=1)).strftime(leave_service.DATE_FORMAT), "Pre-approved annual")
    lr_emp2 = leave_service.get_leave_requests(employee_id=EMP_RPT_ID_2, status='Pending')[0]
    leave_service.approve_leave_request(lr_emp2['id'], APPROVER_RPT_ID)
    
    # Emp3: Pending sick leave for today
    leave_service.apply_for_leave(EMP_RPT_ID_3, LT_SICK_RPT_ID,
                                  today.strftime(leave_service.DATE_FORMAT),
                                  (today + timedelta(days=2)).strftime(leave_service.DATE_FORMAT), "Sudden illness")
    print("Seeded leave data.")
    print("Test data seeding complete.")


def main_test_flow():
    print("--- Starting Reporting Module Test ---")
    setup_database_and_base_data() # Ensures DB, tables, base roles/users
    clear_test_data() # Clear data from previous specific test runs of this module
    seed_specific_data_for_reports() # Add fresh data for this test run

    today = date.today()
    yesterday = today - timedelta(days=1)
    next_week_start = today + timedelta(days=7-today.weekday())
    next_week_end = next_week_start + timedelta(days=6)


    # --- Test reporting_service.py directly ---
    print("\n\n*** Testing reporting_service.py directly ***")

    # 1. Daily Attendance Report
    print(f"\n1. Daily Attendance Report for {today.strftime(reporting_service.DATE_FORMAT)} (Service):")
    daily_att_report = reporting_service.get_daily_attendance_report(today)
    assert len(daily_att_report) >= 2 # Emp1 (clocked out) and Emp2 (clocked in)
    print(f"  Found {len(daily_att_report)} records.")
    for r in daily_att_report: print(f"    {r['employee_name']} - In: {r['clock_in_time']}, Out: {r['clock_out_time']}, Dur: {r['duration']}")

    # 2. Employee Attendance Summary
    print(f"\n2. Employee Attendance Summary for EmpID {EMP_RPT_ID_1} (Service):")
    summary_emp1 = reporting_service.get_employee_attendance_summary(EMP_RPT_ID_1, yesterday, today)
    assert summary_emp1['total_days_present'] == 2
    assert summary_emp1['total_duration_seconds'] > 0 
    print(f"  Summary for {EMP_RPT_ID_1}: Days Present={summary_emp1['total_days_present']}, Total Hours={summary_emp1['total_hours_worked_str']}")

    # 3. Leave Report
    print("\n3. Leave Report (Service):")
    leave_report_all = reporting_service.get_leave_report(yesterday, next_week_end) # Wide range
    assert len(leave_report_all) >= 2 # Emp2 (Approved), Emp3 (Pending)
    print(f"  Found {len(leave_report_all)} leave records in range.")
    
    leave_report_approved_emp2 = reporting_service.get_leave_report(yesterday, today, employee_id=EMP_RPT_ID_2, status='Approved')
    assert len(leave_report_approved_emp2) == 1
    assert leave_report_approved_emp2[0]['employee_code'] == EMP_RPT_CODE_2
    print(f"  Found {len(leave_report_approved_emp2)} approved leave for {EMP_RPT_CODE_2} in range.")

    # 4. Absentee Report (Optional - Basic)
    print(f"\n4. Absentee Report for {today.strftime(reporting_service.DATE_FORMAT)} (Service):")
    # Expected: EMP_RPT_3 is absent (has pending leave, not approved)
    # EMP_RPT_1 has attendance. EMP_RPT_2 has attendance (still clocked in) AND approved leave.
    # The current absentee logic will count EMP_RPT_2 as NOT absent because of attendance.
    # If EMP_RPT_2 had NO attendance but approved leave, they would also NOT be absent.
    abs_report = reporting_service.get_absentee_report(today)
    print(f"  Found {len(abs_report)} absentee(s):")
    is_emp3_absent = False
    for emp_abs in abs_report:
        print(f"    - {emp_abs['first_name']} {emp_abs['last_name']} ({emp_abs['employee_code']})")
        if emp_abs['employee_code'] == EMP_RPT_CODE_3 : is_emp3_absent = True
    assert is_emp3_absent # EMP_RPT_3 should be absent

    print("\n*** Direct service tests completed successfully. ***")

    # --- Test placeholder UI functions from reporting_view.py ---
    print("\n\n*** Testing placeholder UI functions from reporting_view.py ***")

    # 1. Daily Attendance Report via UI Handler
    reporting_view.handle_generate_daily_attendance_report_click(today.strftime(reporting_service.DATE_FORMAT))

    # 2. Employee Summary via UI Handler
    reporting_view.handle_generate_employee_summary_click(EMP_RPT_ID_1, yesterday.strftime(reporting_service.DATE_FORMAT), today.strftime(reporting_service.DATE_FORMAT))

    # 3. Leave Report via UI Handler
    reporting_view.handle_generate_leave_report_click(
        start_date_str=yesterday.strftime(reporting_service.DATE_FORMAT),
        end_date_str=next_week_end.strftime(reporting_service.DATE_FORMAT),
        status='Pending' 
    )
    
    # 4. Absentee Report via UI Handler
    reporting_view.handle_generate_absentee_report_click(today.strftime(reporting_service.DATE_FORMAT))

    print("\n*** Placeholder UI function tests completed. ***")
    print("\n--- Reporting Module Test Completed Successfully ---")

if __name__ == "__main__":
    main_test_flow()
