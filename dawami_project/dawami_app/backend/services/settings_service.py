import sqlite3
import os
from datetime import datetime

# Database path configuration
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

DATE_FORMAT = "%Y-%m-%d" # For holiday dates
TIME_FORMAT = "%H:%M" # For work schedule times

def get_db_connection():
    """Creates and returns a database connection."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- SystemSettings ---
def get_setting(setting_key):
    """Retrieves a setting value by its key."""
    sql = "SELECT setting_value FROM SystemSettings WHERE setting_key = ?"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (setting_key,))
        row = cursor.fetchone()
        return row['setting_value'] if row else None
    except sqlite3.Error as e:
        print(f"Database error getting setting '{setting_key}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def set_setting(setting_key, setting_value, description=None):
    """Sets (inserts or updates) a setting."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM SystemSettings WHERE setting_key = ?", (setting_key,))
        existing = cursor.fetchone()
        if existing:
            # Update existing setting
            if description is not None:
                sql_update = "UPDATE SystemSettings SET setting_value = ?, description = ? WHERE setting_key = ?"
                cursor.execute(sql_update, (setting_value, description, setting_key))
            else: # Keep existing description if new one not provided
                sql_update = "UPDATE SystemSettings SET setting_value = ? WHERE setting_key = ?"
                cursor.execute(sql_update, (setting_value, setting_key))
        else:
            # Insert new setting
            sql_insert = "INSERT INTO SystemSettings (setting_key, setting_value, description) VALUES (?, ?, ?)"
            cursor.execute(sql_insert, (setting_key, setting_value, description))
        conn.commit()
        print(f"Setting '{setting_key}' successfully set to '{setting_value}'.")
        return True
    except sqlite3.Error as e:
        print(f"Database error setting setting '{setting_key}': {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_all_settings():
    """Retrieves all settings."""
    sql = "SELECT setting_key, setting_value, description FROM SystemSettings ORDER BY setting_key"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        settings = {row['setting_key']: {'value': row['setting_value'], 'description': row['description']} for row in cursor.fetchall()}
        return settings
    except sqlite3.Error as e:
        print(f"Database error getting all settings: {e}")
        return {}
    finally:
        if conn:
            conn.close()

# --- WorkSchedules ---
def add_work_schedule(schedule_name, expected_start_time_str, expected_end_time_str, grace_period_minutes=0):
    """Adds a new work schedule. Times should be 'HH:MM'."""
    # Basic validation for time format
    try:
        datetime.strptime(expected_start_time_str, TIME_FORMAT)
        datetime.strptime(expected_end_time_str, TIME_FORMAT)
    except ValueError:
        print(f"Error: Invalid time format for schedule '{schedule_name}'. Use HH:MM.")
        return None

    sql = "INSERT INTO WorkSchedules (schedule_name, expected_start_time, expected_end_time, grace_period_minutes) VALUES (?, ?, ?, ?)"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (schedule_name, expected_start_time_str, expected_end_time_str, grace_period_minutes))
        conn.commit()
        schedule_id = cursor.lastrowid
        print(f"Work schedule '{schedule_name}' added successfully with ID: {schedule_id}.")
        return schedule_id
    except sqlite3.IntegrityError as e:
        print(f"Error adding work schedule '{schedule_name}': {e}. Name likely already exists.")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding work schedule '{schedule_name}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_work_schedule(schedule_id):
    """Retrieves a work schedule by its ID."""
    sql = "SELECT * FROM WorkSchedules WHERE id = ?"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (schedule_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Database error getting work schedule ID {schedule_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_work_schedules():
    """Retrieves all work schedules."""
    sql = "SELECT * FROM WorkSchedules ORDER BY schedule_name"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        schedules = [dict(row) for row in cursor.fetchall()]
        return schedules
    except sqlite3.Error as e:
        print(f"Database error getting all work schedules: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_work_schedule(schedule_id, schedule_name=None, expected_start_time_str=None, expected_end_time_str=None, grace_period_minutes=None):
    """Updates an existing work schedule."""
    fields_to_update = []
    params = []

    if schedule_name is not None:
        fields_to_update.append("schedule_name = ?")
        params.append(schedule_name)
    if expected_start_time_str is not None:
        try: datetime.strptime(expected_start_time_str, TIME_FORMAT)
        except ValueError: print(f"Invalid start time format: {expected_start_time_str}"); return False
        fields_to_update.append("expected_start_time = ?")
        params.append(expected_start_time_str)
    if expected_end_time_str is not None:
        try: datetime.strptime(expected_end_time_str, TIME_FORMAT)
        except ValueError: print(f"Invalid end time format: {expected_end_time_str}"); return False
        fields_to_update.append("expected_end_time = ?")
        params.append(expected_end_time_str)
    if grace_period_minutes is not None:
        fields_to_update.append("grace_period_minutes = ?")
        params.append(grace_period_minutes)

    if not fields_to_update:
        print("No fields provided for work schedule update.")
        return False

    sql = f"UPDATE WorkSchedules SET {', '.join(fields_to_update)} WHERE id = ?"
    params.append(schedule_id)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM WorkSchedules WHERE id = ?", (schedule_id,))
        if not cursor.fetchone():
            print(f"Work schedule ID {schedule_id} not found for update.")
            return False
        
        cursor.execute(sql, tuple(params))
        conn.commit()
        print(f"Work schedule ID {schedule_id} updated successfully.")
        return True
    except sqlite3.IntegrityError as e:
        print(f"Error updating work schedule ID {schedule_id}: {e}. Name likely already exists.")
        return False
    except sqlite3.Error as e:
        print(f"Database error updating work schedule ID {schedule_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_work_schedule(schedule_id):
    """Deletes a work schedule. Employees assigned will have work_schedule_id set to NULL."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM WorkSchedules WHERE id = ?", (schedule_id,))
        if not cursor.fetchone():
            print(f"Work schedule ID {schedule_id} not found for deletion.")
            return False

        sql = "DELETE FROM WorkSchedules WHERE id = ?"
        cursor.execute(sql, (schedule_id,))
        conn.commit()
        print(f"Work schedule ID {schedule_id} deleted successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Database error deleting work schedule ID {schedule_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- Holidays ---
def add_holiday(name, date_str, description=None):
    """Adds a new holiday. Date should be 'YYYY-MM-DD'."""
    try:
        datetime.strptime(date_str, DATE_FORMAT) # Validate date format
    except ValueError:
        print(f"Error: Invalid date format for holiday '{name}'. Use YYYY-MM-DD.")
        return None
        
    sql = "INSERT INTO Holidays (name, date, description) VALUES (?, ?, ?)"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (name, date_str, description))
        conn.commit()
        holiday_id = cursor.lastrowid
        print(f"Holiday '{name}' on {date_str} added successfully with ID: {holiday_id}.")
        return holiday_id
    except sqlite3.IntegrityError as e: # Handles UNIQUE constraint on date
        print(f"Error adding holiday '{name}' on {date_str}: {e}. Date likely already exists.")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding holiday '{name}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_holidays(year=None):
    """Retrieves holidays, optionally filtered by year."""
    params = []
    sql = "SELECT * FROM Holidays"
    if year:
        sql += " WHERE strftime('%Y', date) = ?"
        params.append(str(year))
    sql += " ORDER BY date"
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error fetching holidays: {e}")
        return []
    finally:
        if conn:
            conn.close()

def delete_holiday(holiday_id_or_date_str):
    """Deletes a holiday by its ID or date string ('YYYY-MM-DD')."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        deleted = False
        # Try to delete by ID if it's an integer
        if isinstance(holiday_id_or_date_str, int) or holiday_id_or_date_str.isdigit():
            cursor.execute("DELETE FROM Holidays WHERE id = ?", (int(holiday_id_or_date_str),))
            if cursor.rowcount > 0:
                deleted = True
                print(f"Holiday ID {holiday_id_or_date_str} deleted successfully.")
        
        # If not deleted by ID, try by date string
        if not deleted:
            try:
                datetime.strptime(holiday_id_or_date_str, DATE_FORMAT) # Validate format
                cursor.execute("DELETE FROM Holidays WHERE date = ?", (holiday_id_or_date_str,))
                if cursor.rowcount > 0:
                    deleted = True
                    print(f"Holiday on date {holiday_id_or_date_str} deleted successfully.")
            except ValueError: # Not a valid date string if we reach here after failing int conversion
                pass

        if not deleted:
            print(f"No holiday found with ID or date '{holiday_id_or_date_str}' to delete.")
            return False
            
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error deleting holiday '{holiday_id_or_date_str}': {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Settings Service Module - Direct Execution (for testing)")
    if not os.path.exists(DB_FILE): print("DB file not found. Run setup."); sys.exit(1)

    # SystemSettings Tests
    set_setting("company_name", "Dawami Corp", "Official name of the company")
    set_setting("default_language", "en_US")
    print("Company Name:", get_setting("company_name"))
    all_s = get_all_settings()
    print("All Settings:", all_s)

    # WorkSchedules Tests
    ws_id = add_work_schedule("Standard 9-5", "09:00", "17:00", 15)
    if ws_id:
        print("Added WS:", get_work_schedule(ws_id))
        update_work_schedule(ws_id, grace_period_minutes=20)
        print("Updated WS:", get_work_schedule(ws_id))
    add_work_schedule("Part-Time Morning", "08:00", "12:00")
    print("All WS:", get_all_work_schedules())
    if ws_id: delete_work_schedule(ws_id) # Clean up

    # Holidays Tests
    h_id1 = add_holiday("New Year's Day", f"{datetime.now().year}-01-01")
    add_holiday("Local Holiday", f"{datetime.now().year}-03-15")
    if h_id1:
        print(f"Holiday by ID {h_id1}: {get_holidays(year=datetime.now().year)}") # Should show one
    print("All holidays this year:", get_holidays(year=datetime.now().year))
    delete_holiday(f"{datetime.now().year}-03-15")
    print("Holidays after delete:", get_holidays(year=datetime.now().year))
