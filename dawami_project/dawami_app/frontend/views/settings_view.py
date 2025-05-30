import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import settings_service

# These functions simulate what would be called by actual UI event handlers.

# --- SystemSettings UI Handlers ---
def handle_get_setting_click(setting_key):
    print(f"\n--- Handling Get Setting Click (Key: {setting_key}) ---")
    value = settings_service.get_setting(setting_key)
    if value is not None:
        print(f"UI: Setting '{setting_key}' = '{value}'")
    else:
        print(f"UI: Setting '{setting_key}' not found.")
    return value

def handle_set_setting_click(setting_key, setting_value, description=None):
    print(f"\n--- Handling Set Setting Click (Key: {setting_key}, Value: {setting_value}) ---")
    success = settings_service.set_setting(setting_key, setting_value, description)
    if success:
        print(f"UI: Setting '{setting_key}' updated successfully.")
    else:
        print(f"UI: Failed to update setting '{setting_key}'.")
    return success

def handle_get_all_settings_click():
    print("\n--- Handling Get All Settings Click ---")
    settings = settings_service.get_all_settings()
    if settings:
        print(f"UI: All System Settings ({len(settings)}):")
        for key, data in settings.items():
            print(f"  - {key}: {data['value']} (Desc: {data.get('description', 'N/A')})")
    else:
        print("UI: No system settings found or error retrieving them.")
    return settings

# --- WorkSchedules UI Handlers ---
def handle_add_work_schedule_click(name, start_time_str, end_time_str, grace_minutes=0):
    print(f"\n--- Handling Add Work Schedule Click (Name: {name}) ---")
    schedule_id = settings_service.add_work_schedule(name, start_time_str, end_time_str, grace_minutes)
    if schedule_id:
        print(f"UI: Work Schedule '{name}' added with ID: {schedule_id}")
    else:
        print(f"UI: Failed to add work schedule '{name}'.")
    return schedule_id

def handle_get_all_work_schedules_click():
    print("\n--- Handling Get All Work Schedules Click ---")
    schedules = settings_service.get_all_work_schedules()
    if schedules:
        print(f"UI: All Work Schedules ({len(schedules)}):")
        for ws in schedules:
            print(f"  ID: {ws['id']}, Name: {ws['schedule_name']}, Start: {ws['expected_start_time']}, "
                  f"End: {ws['expected_end_time']}, Grace: {ws['grace_period_minutes']} min")
    else:
        print("UI: No work schedules found or error retrieving them.")
    return schedules

def handle_update_work_schedule_click(schedule_id, update_data):
    print(f"\n--- Handling Update Work Schedule Click (ID: {schedule_id}) ---")
    print(f"UI: Attempting to update schedule ID {schedule_id} with data: {update_data}")
    success = settings_service.update_work_schedule(schedule_id, **update_data) # Pass dict as kwargs
    if success:
        print(f"UI: Work Schedule ID {schedule_id} updated successfully.")
    else:
        print(f"UI: Failed to update work schedule ID {schedule_id}.")
    return success

def handle_delete_work_schedule_click(schedule_id):
    print(f"\n--- Handling Delete Work Schedule Click (ID: {schedule_id}) ---")
    success = settings_service.delete_work_schedule(schedule_id)
    if success:
        print(f"UI: Work Schedule ID {schedule_id} deleted successfully.")
    else:
        print(f"UI: Failed to delete work schedule ID {schedule_id}.")
    return success

# --- Holidays UI Handlers ---
def handle_add_holiday_click(name, date_str, description=None):
    print(f"\n--- Handling Add Holiday Click (Name: {name}, Date: {date_str}) ---")
    holiday_id = settings_service.add_holiday(name, date_str, description)
    if holiday_id:
        print(f"UI: Holiday '{name}' on {date_str} added with ID: {holiday_id}")
    else:
        print(f"UI: Failed to add holiday '{name}'.")
    return holiday_id

def handle_get_holidays_click(year=None):
    print(f"\n--- Handling Get Holidays Click (Year: {year if year else 'All'}) ---")
    holidays = settings_service.get_holidays(year)
    if holidays:
        print(f"UI: Holidays ({len(holidays)}):")
        for h in holidays:
            print(f"  ID: {h['id']}, Name: {h['name']}, Date: {h['date']}, Desc: {h.get('description', 'N/A')}")
    else:
        print("UI: No holidays found or error retrieving them.")
    return holidays

def handle_delete_holiday_click(holiday_id_or_date_str):
    print(f"\n--- Handling Delete Holiday Click (ID/Date: {holiday_id_or_date_str}) ---")
    success = settings_service.delete_holiday(holiday_id_or_date_str)
    if success:
        print(f"UI: Holiday '{holiday_id_or_date_str}' deleted successfully.")
    else:
        print(f"UI: Failed to delete holiday '{holiday_id_or_date_str}'.")
    return success


if __name__ == '__main__':
    print("Settings View Module - Placeholder UI Handlers (Direct Demonstration)")
    db_file = os.path.join(PROJECT_ROOT, "dawami_app", "database", "dawami_dev.db")
    if not os.path.exists(db_file):
        print(f"WARNING: Database file not found at {db_file}. Demo may fail or create an empty DB.")
        print("Please run 'scripts/database_setup.py' first.")
        # Attempt to run database_setup.py
        # setup_script_path = os.path.join(PROJECT_ROOT, "scripts", "database_setup.py")
        # try:
        #     import subprocess
        #     subprocess.run([sys.executable, setup_script_path], check=True)
        # except Exception as e:
        #     print(f"Failed to run database_setup.py automatically: {e}")
        #     sys.exit(1)


    # System Settings Demo
    handle_set_setting_click("app_version", "1.0.0-demo", "Current application version")
    handle_get_setting_click("app_version")
    handle_get_all_settings_click()

    # Work Schedules Demo
    ws_id = handle_add_work_schedule_click("Flexi Shift", "10:00", "18:00", 30)
    handle_get_all_work_schedules_click()
    if ws_id:
        handle_update_work_schedule_click(ws_id, {'grace_period_minutes': 35, 'schedule_name': "Flexi Shift Plus"})
        handle_delete_work_schedule_click(ws_id)
    
    # Holidays Demo
    from datetime import date, timedelta
    today = date.today()
    h_id = handle_add_holiday_click("Demo Day", today.strftime(settings_service.DATE_FORMAT), "A day for demos")
    handle_get_holidays_click(year=today.year)
    if h_id:
        handle_delete_holiday_click(str(h_id)) # Test deletion by ID
    
    next_holiday_date = (today + timedelta(days=60)).strftime(settings_service.DATE_FORMAT)
    handle_add_holiday_click("Future Demo Day", next_holiday_date)
    handle_delete_holiday_click(next_holiday_date) # Test deletion by date string

    print("\nSettings View Module Demonstration Complete.")
