import sqlite3
import os
from datetime import datetime, date

# Database path configuration
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S" # For storing and parsing datetime
DATE_FORMAT = "%Y-%m-%d" # For storing and parsing date

def get_db_connection():
    """Creates and returns a database connection."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def clock_in(employee_id, clock_in_time_dt=None, notes=None, source='manual'):
    """
    Records a clock-in event for an employee.
    :param employee_id: ID of the employee.
    :param clock_in_time_dt: datetime object for clock-in. Defaults to current time.
    :param notes: Optional notes for the clock-in.
    :param source: Source of the clock-in (e.g., 'manual', 'fingerprint').
    :return: The ID of the new attendance log entry or None on failure.
    """
    if clock_in_time_dt is None:
        clock_in_time_dt = datetime.now()
    
    clock_in_time_str = clock_in_time_dt.strftime(DATETIME_FORMAT)
    attendance_date_str = clock_in_time_dt.strftime(DATE_FORMAT)

    # Optional: Check for existing employee (can be enforced by FK constraint too)
    # conn_check = get_db_connection()
    # cursor_check = conn_check.cursor()
    # cursor_check.execute("SELECT id FROM Employees WHERE id = ?", (employee_id,))
    # if not cursor_check.fetchone():
    #     print(f"Clock-in failed: Employee with ID {employee_id} not found.")
    #     conn_check.close()
    #     return None
    # conn_check.close()

    # For this version, we allow multiple clock-ins without checking for open ones.
    # A more advanced version might prevent this or handle it differently.

    sql = """
        INSERT INTO AttendanceLog (employee_id, clock_in_time, attendance_date, notes, source)
        VALUES (?, ?, ?, ?, ?)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (employee_id, clock_in_time_str, attendance_date_str, notes, source))
        conn.commit()
        log_id = cursor.lastrowid
        print(f"Employee ID {employee_id} clocked in successfully at {clock_in_time_str}. Log ID: {log_id}")
        return log_id
    except sqlite3.IntegrityError as e:
        # This would typically be due to employee_id not existing if FK constraints are on.
        print(f"Clock-in failed for employee ID {employee_id} (IntegrityError): {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error during clock-in for employee ID {employee_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_open_attendance(employee_id):
    """
    Finds the most recent open (not clocked-out) attendance record for an employee.
    :param employee_id: ID of the employee.
    :return: A dictionary representing the open log entry, or None if not found.
    """
    sql = """
        SELECT * FROM AttendanceLog
        WHERE employee_id = ? AND clock_out_time IS NULL
        ORDER BY clock_in_time DESC
        LIMIT 1
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (employee_id,))
        open_log = cursor.fetchone()
        if open_log:
            return dict(open_log)
        return None
    except sqlite3.Error as e:
        print(f"Database error fetching open attendance for employee ID {employee_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def clock_out(employee_id, clock_out_time_dt=None, notes=None):
    """
    Records a clock-out event for an employee.
    Updates the most recent open AttendanceLog entry.
    :param employee_id: ID of the employee.
    :param clock_out_time_dt: datetime object for clock-out. Defaults to current time.
    :param notes: Optional notes for the clock-out (can append to existing notes).
    :return: True on successful update, False otherwise.
    """
    open_log = get_open_attendance(employee_id)
    if not open_log:
        print(f"Clock-out failed: No open clock-in record found for employee ID {employee_id}.")
        return False

    if clock_out_time_dt is None:
        clock_out_time_dt = datetime.now()
    
    clock_out_time_str = clock_out_time_dt.strftime(DATETIME_FORMAT)

    # Ensure clock_out_time is after clock_in_time
    clock_in_dt = datetime.strptime(open_log['clock_in_time'], DATETIME_FORMAT)
    if clock_out_time_dt < clock_in_dt:
        print(f"Clock-out failed: Clock-out time ({clock_out_time_str}) cannot be before clock-in time ({open_log['clock_in_time']}).")
        return False

    updated_notes = open_log['notes']
    if notes: # Append new notes if provided
        if updated_notes:
            updated_notes = f"{updated_notes}\nClock-out: {notes}"
        else:
            updated_notes = f"Clock-out: {notes}"
    
    sql = """
        UPDATE AttendanceLog
        SET clock_out_time = ?, notes = ?
        WHERE id = ?
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (clock_out_time_str, updated_notes, open_log['id']))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Employee ID {employee_id} clocked out successfully at {clock_out_time_str} for Log ID: {open_log['id']}.")
            return True
        else:
            # Should not happen if open_log was found, but good for robustness
            print(f"Clock-out failed: Could not update record for Log ID: {open_log['id']}.")
            return False
    except sqlite3.Error as e:
        print(f"Database error during clock-out for employee ID {employee_id}, Log ID {open_log['id']}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_attendance_records(employee_id=None, start_date_obj=None, end_date_obj=None):
    """
    Retrieves attendance records, optionally filtered by employee and/or date range.
    :param employee_id: Optional ID of the employee.
    :param start_date_obj: Optional date object for the start of the range.
    :param end_date_obj: Optional date object for the end of the range.
    :return: A list of attendance log objects (dictionaries).
    """
    params = []
    sql_clauses = []

    if employee_id is not None:
        sql_clauses.append("employee_id = ?")
        params.append(employee_id)
    
    # Dates are stored as TEXT YYYY-MM-DD, so string comparison works.
    if start_date_obj is not None:
        sql_clauses.append("attendance_date >= ?")
        params.append(start_date_obj.strftime(DATE_FORMAT))
    
    if end_date_obj is not None:
        sql_clauses.append("attendance_date <= ?")
        params.append(end_date_obj.strftime(DATE_FORMAT))

    sql = "SELECT * FROM AttendanceLog"
    if sql_clauses:
        sql += " WHERE " + " AND ".join(sql_clauses)
    sql += " ORDER BY attendance_date DESC, clock_in_time DESC"

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        records = [dict(row) for row in cursor.fetchall()]
        return records
    except sqlite3.Error as e:
        print(f"Database error fetching attendance records: {e}")
        return []
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    print("Attendance Service Module - Direct Execution (for testing)")

    if not os.path.exists(DB_FILE):
        print(f"Database file not found at {DB_FILE}. Please run scripts/database_setup.py and scripts/seed_data.py first.")
        sys.exit(1)
    else:
        print(f"Database file found at {DB_FILE}.")

    # --- You would need an employee_id from your Employees table to test ---
    # For example, if you have an employee with ID 1 (created by seed_data.py or employee_service.py)
    TEST_EMPLOYEE_ID = 1 # Make sure this employee exists

    # Check if test employee exists
    conn_check = get_db_connection()
    cursor_check = conn_check.cursor()
    cursor_check.execute("SELECT id FROM Employees WHERE id = ?", (TEST_EMPLOYEE_ID,))
    if not cursor_check.fetchone():
        print(f"Cannot run tests: Employee with ID {TEST_EMPLOYEE_ID} not found. Seed data or add employee first.")
        conn_check.close()
    else:
        conn_check.close()
        print(f"Running tests for Employee ID: {TEST_EMPLOYEE_ID}")

        # 1. Clock In
        print("\n--- Test Clock-In ---")
        clock_in_log_id = clock_in(TEST_EMPLOYEE_ID, notes="Starting the day")
        if clock_in_log_id:
            # 2. Get Open Attendance
            print("\n--- Test Get Open Attendance (after clock-in) ---")
            open_att = get_open_attendance(TEST_EMPLOYEE_ID)
            if open_att:
                print(f"Open attendance found: ID {open_att['id']}, In: {open_att['clock_in_time']}")
                assert open_att['id'] == clock_in_log_id
                assert open_att['clock_out_time'] is None
            else:
                print("No open attendance found, something is wrong.")

            # 3. Clock Out
            print("\n--- Test Clock-Out ---")
            # Simulate some time passed
            import time
            time.sleep(1) # Ensure clock_out_time is slightly after clock_in_time for realistic data
            clock_out_success = clock_out(TEST_EMPLOYEE_ID, notes="Ending the day")
            if clock_out_success:
                print("Clock-out successful.")
            else:
                print("Clock-out failed.")
            
            # 4. Get Open Attendance (should be None now)
            print("\n--- Test Get Open Attendance (after clock-out) ---")
            open_att_after_out = get_open_attendance(TEST_EMPLOYEE_ID)
            if open_att_after_out:
                print(f"ERROR: Open attendance still found: {open_att_after_out}")
            else:
                print("Correctly no open attendance found.")
        
        # 5. Test Clock-Out again (should fail as there's no open session)
        print("\n--- Test Clock-Out (again, should fail) ---")
        clock_out_fail = clock_out(TEST_EMPLOYEE_ID, notes="Trying to clock out again")
        if not clock_out_fail:
            print("Correctly failed to clock out (no open session).")
        else:
            print("ERROR: Clocked out successfully when it should have failed.")

        # 6. Get Attendance Records
        print("\n--- Test Get Attendance Records ---")
        today = date.today()
        records_today = get_attendance_records(employee_id=TEST_EMPLOYEE_ID, start_date_obj=today, end_date_obj=today)
        print(f"Found {len(records_today)} records for employee {TEST_EMPLOYEE_ID} today:")
        for rec in records_today:
            print(f"  Log ID: {rec['id']}, In: {rec['clock_in_time']}, Out: {rec['clock_out_time']}, Date: {rec['attendance_date']}")
        
        all_records_emp = get_attendance_records(employee_id=TEST_EMPLOYEE_ID)
        print(f"\nFound {len(all_records_emp)} total records for employee {TEST_EMPLOYEE_ID}.")
        
        all_records_overall = get_attendance_records()
        print(f"\nFound {len(all_records_overall)} total records for all employees.")

        # Clean up test entry (optional, or use a dedicated test DB)
        # if clock_in_log_id:
        #     conn_del = get_db_connection()
        #     cursor_del = conn_del.cursor()
        #     cursor_del.execute("DELETE FROM AttendanceLog WHERE id = ?", (clock_in_log_id,))
        #     conn_del.commit()
        #     conn_del.close()
        #     print(f"\nCleaned up test attendance log ID: {clock_in_log_id}")
