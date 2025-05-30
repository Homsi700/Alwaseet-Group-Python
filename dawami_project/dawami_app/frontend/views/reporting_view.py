import os
import sys
from datetime import datetime, date # For testing date inputs

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import reporting_service

# These functions simulate what would be called by actual UI event handlers.

def handle_generate_daily_attendance_report_click(report_date_str):
    """Simulates generating a daily attendance report."""
    print(f"\n--- Handling Generate Daily Attendance Report Click (Date: {report_date_str}) ---")
    try:
        report_date_obj = datetime.strptime(report_date_str, reporting_service.DATE_FORMAT).date()
    except ValueError:
        print(f"UI Error: Invalid date format '{report_date_str}'. Please use YYYY-MM-DD.")
        return []
    
    report_data = reporting_service.get_daily_attendance_report(report_date_obj)
    if report_data:
        print(f"UI: Daily Attendance Report for {report_date_str} ({len(report_data)} entries):")
        for row in report_data:
            print(f"  Emp: {row['employee_name']} ({row['employee_code']}), "
                  f"In: {row['clock_in_time']}, Out: {row['clock_out_time']}, "
                  f"Duration: {row['duration']}, Notes: {row.get('notes', 'N/A')}, Source: {row.get('source', 'N/A')}")
    elif report_data is not None: # Empty list
        print(f"UI: No attendance records found for {report_date_str}.")
    else: # None was returned
        print("UI: Error generating daily attendance report.")
    return report_data

def handle_generate_employee_summary_click(employee_id, start_date_str, end_date_str):
    """Simulates generating an employee attendance summary."""
    print(f"\n--- Handling Generate Employee Summary Click (EmpID: {employee_id}) ---")
    print(f"UI Params: Start: {start_date_str}, End: {end_date_str}")
    try:
        start_date_obj = datetime.strptime(start_date_str, reporting_service.DATE_FORMAT).date()
        end_date_obj = datetime.strptime(end_date_str, reporting_service.DATE_FORMAT).date()
    except ValueError:
        print(f"UI Error: Invalid date format. Please use YYYY-MM-DD.")
        return None
        
    summary_data = reporting_service.get_employee_attendance_summary(employee_id, start_date_obj, end_date_obj)
    if summary_data:
        print("UI: Employee Attendance Summary:")
        print(f"  Employee ID: {summary_data['employee_id']}")
        print(f"  Period: {summary_data['start_date']} to {summary_data['end_date']}")
        print(f"  Total Days Present: {summary_data['total_days_present']}")
        print(f"  Total Hours Worked: {summary_data['total_hours_worked_str']}")
        print(f"  Late Arrivals: {summary_data['late_arrivals']}")
        print(f"  Early Departures: {summary_data['early_departures']}")
    else: # None or empty dict if error
        print("UI: Error generating employee attendance summary or no data.")
    return summary_data

def handle_generate_leave_report_click(start_date_str, end_date_str, employee_id=None, leave_type_id=None, status=None):
    """Simulates generating a leave report."""
    print("\n--- Handling Generate Leave Report Click ---")
    print(f"UI Params: EmployeeID: {employee_id}, LeaveTypeID: {leave_type_id}, Status: {status}, "
          f"Start: {start_date_str}, End: {end_date_str}")
    try:
        start_date_obj = datetime.strptime(start_date_str, reporting_service.DATE_FORMAT).date()
        end_date_obj = datetime.strptime(end_date_str, reporting_service.DATE_FORMAT).date()
    except ValueError:
        print(f"UI Error: Invalid date format. Please use YYYY-MM-DD.")
        return []

    report_data = reporting_service.get_leave_report(start_date_obj, end_date_obj, employee_id, leave_type_id, status)
    if report_data:
        print(f"UI: Leave Report ({len(report_data)} entries):")
        for row in report_data:
            print(f"  Emp: {row['employee_name']} ({row['employee_code']}), Type: {row['leave_type_name']}, "
                  f"Dates: {row['start_date']} to {row['end_date']}, Status: {row['status']}, "
                  f"Requested: {row['request_date']}, Approver: {row.get('approver_username', 'N/A')}")
    elif report_data is not None: # Empty list
        print("UI: No leave records found matching criteria.")
    else: # None
        print("UI: Error generating leave report.")
    return report_data

def handle_generate_absentee_report_click(report_date_str):
    """Simulates generating an absentee report."""
    print(f"\n--- Handling Generate Absentee Report Click (Date: {report_date_str}) ---")
    try:
        report_date_obj = datetime.strptime(report_date_str, reporting_service.DATE_FORMAT).date()
    except ValueError:
        print(f"UI Error: Invalid date format '{report_date_str}'. Please use YYYY-MM-DD.")
        return []
        
    absentee_data = reporting_service.get_absentee_report(report_date_obj)
    if absentee_data:
        print(f"UI: Absentee Report for {report_date_str} ({len(absentee_data)} employees):")
        for emp in absentee_data:
            print(f"  - {emp['first_name']} {emp['last_name']} ({emp['employee_code']})")
    elif absentee_data is not None: # Empty list
        print(f"UI: No absentees found for {report_date_str} (all present or on approved leave).")
    else: # None
        print("UI: Error generating absentee report.")
    return absentee_data


if __name__ == '__main__':
    print("Reporting View Module - Placeholder UI Handlers (Direct Demonstration)")
    db_file = os.path.join(PROJECT_ROOT, "dawami_app", "database", "dawami_dev.db")
    if not os.path.exists(db_file):
        print(f"WARNING: Database file not found at {db_file}. Demo may fail.")
        print("Please run setup and seed scripts for relevant modules first.")
        sys.exit(1)

    # Assuming employee ID 1 exists, and some data has been seeded by other module tests or seed_data.py
    TEST_EMP_ID = 1 
    today_str = date.today().strftime(reporting_service.DATE_FORMAT)
    seven_days_ago_str = (date.today() - timedelta(days=7)).strftime(reporting_service.DATE_FORMAT)

    # 1. Daily Attendance Report
    handle_generate_daily_attendance_report_click(today_str)
    
    # 2. Employee Attendance Summary
    handle_generate_employee_summary_click(TEST_EMP_ID, seven_days_ago_str, today_str)

    # 3. Leave Report (e.g., all approved leaves in the last week)
    handle_generate_leave_report_click(seven_days_ago_str, today_str, status='Approved')
    
    # 4. Absentee Report for today
    handle_generate_absentee_report_click(today_str)

    print("\nReporting View Module Demonstration Complete.")
