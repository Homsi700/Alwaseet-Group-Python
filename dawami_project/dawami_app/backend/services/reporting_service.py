import sqlite3
import os
from datetime import datetime, timedelta, date

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

def _calculate_duration(clock_in_str, clock_out_str):
    """
    Calculates duration between clock-in and clock-out times.
    Returns duration as a string "HH:MM:SS" or "N/A" or "Open".
    """
    if not clock_in_str:
        return "N/A" # Should not happen if record exists
    
    if not clock_out_str:
        return "Open" # Still clocked in

    try:
        clock_in_dt = datetime.strptime(clock_in_str, DATETIME_FORMAT)
        clock_out_dt = datetime.strptime(clock_out_str, DATETIME_FORMAT)
        if clock_out_dt < clock_in_dt:
            return "Invalid (Out < In)" # Error case
        
        duration_delta = clock_out_dt - clock_in_dt
        
        total_seconds = int(duration_delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    except ValueError:
        return "Error calculating" # Should not happen with valid DATETIME_FORMAT

def get_daily_attendance_report(report_date_obj):
    """
    Fetches daily attendance report for a given date.
    :param report_date_obj: A date object for the report.
    :return: List of report row dictionaries.
    """
    report_date_str = report_date_obj.strftime(DATE_FORMAT)
    sql = """
        SELECT 
            e.first_name || ' ' || e.last_name as employee_name,
            e.employee_code,
            al.clock_in_time,
            al.clock_out_time,
            al.notes,
            al.source
        FROM AttendanceLog al
        JOIN Employees e ON al.employee_id = e.id
        WHERE al.attendance_date = ?
        ORDER BY e.last_name, e.first_name, al.clock_in_time
    """
    conn = get_db_connection()
    report_data = []
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (report_date_str,))
        for row in cursor.fetchall():
            row_dict = dict(row)
            row_dict['duration'] = _calculate_duration(row_dict.get('clock_in_time'), row_dict.get('clock_out_time'))
            report_data.append(row_dict)
        return report_data
    except sqlite3.Error as e:
        print(f"Database error in get_daily_attendance_report: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_employee_attendance_summary(employee_id, start_date_obj, end_date_obj):
    """
    Generates an attendance summary for a specific employee over a date range.
    Focuses on total hours and days present. Late/early metrics are deferred.
    :param employee_id: ID of the employee.
    :param start_date_obj: Date object for the start of the range.
    :param end_date_obj: Date object for the end of the range.
    :return: A summary dictionary.
    """
    start_date_str = start_date_obj.strftime(DATE_FORMAT)
    end_date_str = end_date_obj.strftime(DATE_FORMAT)

    sql = """
        SELECT
            al.attendance_date,
            al.clock_in_time,
            al.clock_out_time,
            e.work_schedule_id, 
            ws.expected_start_time, -- For future late/early calculation
            ws.expected_end_time   -- For future late/early calculation
        FROM AttendanceLog al
        JOIN Employees e ON al.employee_id = e.id
        LEFT JOIN WorkSchedules ws ON e.work_schedule_id = ws.id
        WHERE al.employee_id = ? 
          AND al.attendance_date >= ? 
          AND al.attendance_date <= ?
        ORDER BY al.attendance_date
    """
    conn = get_db_connection()
    summary = {
        'employee_id': employee_id,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'total_days_present': 0,
        'total_duration_seconds': 0,
        'total_hours_worked_str': "00:00:00",
        'late_arrivals': "N/A (Deferred)", # Placeholder
        'early_departures': "N/A (Deferred)" # Placeholder
    }
    present_dates = set()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, (employee_id, start_date_str, end_date_str))
        
        for row in cursor.fetchall():
            present_dates.add(row['attendance_date'])
            if row['clock_in_time'] and row['clock_out_time']:
                try:
                    cin = datetime.strptime(row['clock_in_time'], DATETIME_FORMAT)
                    cout = datetime.strptime(row['clock_out_time'], DATETIME_FORMAT)
                    if cout > cin:
                        summary['total_duration_seconds'] += (cout - cin).total_seconds()
                except ValueError:
                    pass # Ignore if times are malformed for some reason

        summary['total_days_present'] = len(present_dates)
        
        # Format total_duration_seconds into HH:MM:SS
        tds = int(summary['total_duration_seconds'])
        summary['total_hours_worked_str'] = f"{tds // 3600:02}:{(tds % 3600) // 60:02}:{tds % 60:02}"
        
        return summary
    except sqlite3.Error as e:
        print(f"Database error in get_employee_attendance_summary: {e}")
        return summary # Return partially computed or default summary
    finally:
        if conn:
            conn.close()

def get_leave_report(start_date_obj, end_date_obj, employee_id=None, leave_type_id=None, status=None):
    """
    Fetches leave requests within a date range, with optional filters.
    :param start_date_obj: Date object for start of range.
    :param end_date_obj: Date object for end of range.
    :param employee_id, leave_type_id, status: Optional filters.
    :return: List of leave report row dictionaries.
    """
    start_date_str = start_date_obj.strftime(DATE_FORMAT)
    end_date_str = end_date_obj.strftime(DATE_FORMAT)

    params = [start_date_str, end_date_str]
    sql_clauses = ["lr.start_date <= ? AND lr.end_date >= ?"] # Overlapping range logic can be complex.
                                                            # This is a simple version: request must be active within the period.
                                                            # A more precise one might be:
                                                            # (lr.start_date BETWEEN ? AND ?) OR (lr.end_date BETWEEN ? AND ?) OR 
                                                            # (lr.start_date < ? AND lr.end_date > ?)
                                                            # For now, using: (request starts before/on end_date) AND (request ends after/on start_date)
    sql_clauses = ["lr.start_date <= ? AND lr.end_date >= ?"]
    params = [end_date_str, start_date_str] # Corrected order for this logic


    if employee_id is not None:
        sql_clauses.append("lr.employee_id = ?")
        params.append(employee_id)
    if leave_type_id is not None:
        sql_clauses.append("lr.leave_type_id = ?")
        params.append(leave_type_id)
    if status is not None:
        sql_clauses.append("lr.status = ?")
        params.append(status)

    sql = """
        SELECT 
            e.first_name || ' ' || e.last_name as employee_name,
            e.employee_code,
            lt.type_name as leave_type_name,
            lr.start_date,
            lr.end_date,
            lr.reason,
            lr.status,
            lr.request_date,
            ua.username as approver_username
        FROM LeaveRequests lr
        JOIN Employees e ON lr.employee_id = e.id
        JOIN LeaveTypes lt ON lr.leave_type_id = lt.id
        LEFT JOIN Users ua ON lr.approver_id = ua.id
    """
    if sql_clauses:
        sql += " WHERE " + " AND ".join(sql_clauses)
    sql += " ORDER BY lr.start_date, e.last_name, e.first_name"

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error in get_leave_report: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_absentee_report(report_date_obj):
    """
    (Optional - Basic) Finds employees who were not present and not on approved leave.
    :param report_date_obj: Date object for the report.
    :return: List of absent employee names/codes.
    """
    report_date_str = report_date_obj.strftime(DATE_FORMAT)
    
    # This query is complex. It needs to:
    # 1. Get all active employees.
    # 2. Exclude those with an attendance record on report_date_str.
    # 3. Exclude those with an approved leave request covering report_date_str.
    sql = """
        SELECT e.employee_code, e.first_name, e.last_name
        FROM Employees e
        WHERE e.id NOT IN (
            -- Employees who have an attendance record on the report date
            SELECT DISTINCT al.employee_id 
            FROM AttendanceLog al 
            WHERE al.attendance_date = :report_date
        )
        AND e.id NOT IN (
            -- Employees who have an approved leave request covering the report date
            SELECT DISTINCT lr.employee_id
            FROM LeaveRequests lr
            WHERE lr.status = 'Approved'
            AND lr.start_date <= :report_date
            AND lr.end_date >= :report_date
        )
        -- Assuming there's an 'is_active' field in Employees, or similar concept
        -- For now, let's assume all employees in DB are active for simplicity of this query
        ORDER BY e.last_name, e.first_name;
    """
    # Note: The Users table has is_active, Employees does not in current schema.
    # This query assumes we are checking all employees in the Employees table.
    # A more robust system might have an 'employment_status' (e.g. 'Active', 'Terminated') in Employees.

    conn = get_db_connection()
    absentees = []
    try:
        cursor = conn.cursor()
        # Using named parameters for clarity with the same date
        cursor.execute(sql, {'report_date': report_date_str}) 
        for row in cursor.fetchall():
            absentees.append(dict(row))
        return absentees
    except sqlite3.Error as e:
        print(f"Database error in get_absentee_report: {e}")
        return [] # Return empty list on error
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Reporting Service Module - Direct Execution (for testing)")
    if not os.path.exists(DB_FILE):
        print(f"Database file not found at {DB_FILE}. Please run setup and seed scripts first.")
        sys.exit(1)

    test_date = date.today() # Or a specific date with known data
    
    print(f"\n--- Daily Attendance Report for {test_date.strftime(DATE_FORMAT)} ---")
    daily_att_report = get_daily_attendance_report(test_date)
    if daily_att_report:
        for row in daily_att_report:
            print(f"  Emp: {row['employee_name']} ({row['employee_code']}), In: {row['clock_in_time']}, Out: {row['clock_out_time']}, Duration: {row['duration']}, Notes: {row.get('notes')}")
    else:
        print(f"  No attendance records found for {test_date.strftime(DATE_FORMAT)}.")

    # Assume employee ID 1 exists for summary test
    TEST_EMP_ID = 1
    summary_start_date = test_date - timedelta(days=7)
    summary_end_date = test_date
    print(f"\n--- Employee Attendance Summary for EmpID {TEST_EMP_ID} ({summary_start_date.strftime(DATE_FORMAT)} to {summary_end_date.strftime(DATE_FORMAT)}) ---")
    emp_summary = get_employee_attendance_summary(TEST_EMP_ID, summary_start_date, summary_end_date)
    print(f"  Summary: {emp_summary}")

    print(f"\n--- Leave Report ({summary_start_date.strftime(DATE_FORMAT)} to {summary_end_date.strftime(DATE_FORMAT)}) ---")
    leave_rep = get_leave_report(summary_start_date, summary_end_date, status='Approved')
    if leave_rep:
        for row in leave_rep:
            print(f"  Emp: {row['employee_name']}, Type: {row['leave_type_name']}, Start: {row['start_date']}, End: {row['end_date']}, Status: {row['status']}")
    else:
        print("  No approved leave records in this period.")
        
    print(f"\n--- Absentee Report for {test_date.strftime(DATE_FORMAT)} ---")
    abs_report = get_absentee_report(test_date)
    if abs_report:
        print(f"  Found {len(abs_report)} absent employees (not on attendance, not on approved leave):")
        for emp in abs_report:
            print(f"    - {emp['first_name']} {emp['last_name']} ({emp['employee_code']})")
    else:
        print("  No absentees found or error occurred.")
