import os
import sys
import sqlite3
from datetime import datetime, date, timedelta

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import settings_service
from dawami_app.frontend.views import settings_view # Placeholder UI handlers

DB_DIR = os.path.join(PROJECT_ROOT, "dawami_app", "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

def clear_settings_tables():
    """Clears tables specific to settings module tests for a clean run."""
    print("\nClearing settings-related tables (SystemSettings, WorkSchedules, Holidays)...")
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM SystemSettings")
        cursor.execute("DELETE FROM WorkSchedules") # Note: This might affect Employees if ON DELETE CASCADE was used (it's SET NULL)
        cursor.execute("DELETE FROM Holidays")
        conn.commit()
        print("SystemSettings, WorkSchedules, and Holidays tables cleared.")
    except sqlite3.Error as e:
        print(f"Error clearing settings tables: {e}")
    finally:
        if conn:
            conn.close()

def run_database_setup_if_needed():
    """Ensures the database and all tables, including Holidays, exist."""
    # We need to ensure database_setup.py (which now includes Holidays table) is run.
    # A simple check for one of the later tables (like Holidays) can tell us if it likely ran.
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Holidays';")
        if cursor.fetchone() is None: # Holidays table doesn't exist
            raise sqlite3.DatabaseError("Holidays table not found, running setup.")
        print("Database and Holidays table appear to be set up.")
        
    except (sqlite3.DatabaseError, sqlite3.OperationalError) as e: # Catch if DB itself or table is missing
        print(f"Database check failed ('{e}'). Running/Re-running database_setup.py...")
        try:
            import subprocess
            setup_script_path = os.path.join(PROJECT_ROOT, "scripts", "database_setup.py")
            # Use sys.executable to ensure it's the python from the correct env (ideally venv)
            venv_python = sys.executable 
            if "venv" not in venv_python : # A heuristic, might need adjustment
                 venv_python_candidate = os.path.join(PROJECT_ROOT, "venv", "bin", "python")
                 if os.path.exists(venv_python_candidate):
                     venv_python = venv_python_candidate

            print(f"Using Python interpreter: {venv_python} for database_setup.py.")
            subprocess.run([venv_python, setup_script_path], check=True, cwd=PROJECT_ROOT)
            print("database_setup.py executed successfully.")
        except Exception as proc_e:
            print(f"Error running database_setup.py: {proc_e}. Please run it manually.")
            sys.exit(1)
    finally:
        if conn:
            conn.close()

def main_test_flow():
    print("--- Starting Settings Module Test ---")
    run_database_setup_if_needed() # Ensure Holidays table is created
    clear_settings_tables()

    # --- Test settings_service.py for SystemSettings ---
    print("\n*** Testing SystemSettings (Service) ***")
    assert settings_service.set_setting("company_name", "Dawami Test Co.", "Test Company Name") is True
    assert settings_service.set_setting("overtime_rate", "1.5") is True
    assert settings_service.get_setting("company_name") == "Dawami Test Co."
    assert float(settings_service.get_setting("overtime_rate")) == 1.5
    assert settings_service.get_setting("non_existent_key") is None
    
    all_settings = settings_service.get_all_settings()
    assert len(all_settings) == 2
    assert all_settings['company_name']['value'] == "Dawami Test Co."
    print("SystemSettings service tests passed.")

    # --- Test settings_service.py for WorkSchedules ---
    print("\n*** Testing WorkSchedules (Service) ***")
    ws1_id = settings_service.add_work_schedule("Morning Shift", "08:00", "12:00", 10)
    assert ws1_id is not None
    ws2_id = settings_service.add_work_schedule("Evening Shift", "16:00", "20:00") # Default grace
    assert ws2_id is not None

    ws1_details = settings_service.get_work_schedule(ws1_id)
    assert ws1_details['schedule_name'] == "Morning Shift" and ws1_details['grace_period_minutes'] == 10
    
    all_ws = settings_service.get_all_work_schedules()
    assert len(all_ws) == 2
    
    update_ws1_success = settings_service.update_work_schedule(ws1_id, schedule_name="Early Morning Shift", expected_start_time_str="07:30")
    assert update_ws1_success is True
    ws1_updated_details = settings_service.get_work_schedule(ws1_id)
    assert ws1_updated_details['schedule_name'] == "Early Morning Shift" and ws1_updated_details['expected_start_time'] == "07:30"

    delete_ws2_success = settings_service.delete_work_schedule(ws2_id)
    assert delete_ws2_success is True
    assert settings_service.get_work_schedule(ws2_id) is None
    assert len(settings_service.get_all_work_schedules()) == 1
    print("WorkSchedules service tests passed.")

    # --- Test settings_service.py for Holidays ---
    print("\n*** Testing Holidays (Service) ***")
    year_today = date.today().year
    h1_date_str = f"{year_today}-01-01"
    h2_date_str = f"{year_today}-12-25"
    h1_id = settings_service.add_holiday("New Year Test", h1_date_str, "New Year's Day")
    assert h1_id is not None
    h2_id = settings_service.add_holiday("Christmas Test", h2_date_str)
    assert h2_id is not None
    
    # Test adding duplicate date
    assert settings_service.add_holiday("Duplicate New Year", h1_date_str) is None 

    holidays_this_year = settings_service.get_holidays(year=year_today)
    assert len(holidays_this_year) == 2
    
    all_holidays = settings_service.get_holidays() # Get all, regardless of year
    assert len(all_holidays) == 2 

    delete_h1_by_id_success = settings_service.delete_holiday(h1_id)
    assert delete_h1_by_id_success is True
    assert len(settings_service.get_holidays(year=year_today)) == 1
    
    delete_h2_by_date_success = settings_service.delete_holiday(h2_date_str)
    assert delete_h2_by_date_success is True
    assert len(settings_service.get_holidays(year=year_today)) == 0
    
    assert settings_service.delete_holiday("non-existent-date") is False # Test deleting non-existent
    print("Holidays service tests passed.")

    print("\n*** Direct service tests completed successfully. ***")

    # --- Test placeholder UI functions from settings_view.py ---
    print("\n\n*** Testing placeholder UI functions from settings_view.py ***")
    clear_settings_tables() # Clean again for UI handler tests

    # SystemSettings UI
    settings_view.handle_set_setting_click("ui_company_name", "UI Test Corp", "Set via UI")
    settings_view.handle_get_setting_click("ui_company_name")
    settings_view.handle_get_all_settings_click()

    # WorkSchedules UI
    ui_ws_id = settings_view.handle_add_work_schedule_click("UI Shift", "11:00", "15:00", 5)
    settings_view.handle_get_all_work_schedules_click()
    if ui_ws_id:
        settings_view.handle_update_work_schedule_click(ui_ws_id, {'schedule_name': "UI Shift Updated"})
        settings_view.handle_delete_work_schedule_click(ui_ws_id)
    settings_view.handle_get_all_work_schedules_click() # Should be empty or less one

    # Holidays UI
    ui_h_date = f"{date.today().year}-07-04"
    ui_h_id = settings_view.handle_add_holiday_click("UI Holiday", ui_h_date, "Independence Day via UI")
    settings_view.handle_get_holidays_click(year=date.today().year)
    if ui_h_id:
        settings_view.handle_delete_holiday_click(str(ui_h_id)) # Delete by ID
    settings_view.handle_get_holidays_click(year=date.today().year) # Should be less one or empty

    print("\n*** Placeholder UI function tests completed. ***")
    print("\n--- Settings Module Test Completed Successfully ---")

if __name__ == "__main__":
    main_test_flow()
