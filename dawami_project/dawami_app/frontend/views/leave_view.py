import os
import sys
from datetime import datetime # For testing date inputs

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import leave_service

# These functions simulate what would be called by actual UI event handlers.

def handle_add_leave_type_click(type_name, default_balance=None):
    """Simulates adding a new leave type."""
    print(f"\n--- Handling Add Leave Type Click (Name: {type_name}) ---")
    lt_id = leave_service.add_leave_type(type_name, default_balance)
    if lt_id:
        print(f"UI: Leave Type '{type_name}' added with ID: {lt_id}")
    else:
        print(f"UI: Failed to add leave type '{type_name}'.")
    return lt_id

def handle_get_leave_types_click():
    """Simulates viewing all leave types."""
    print("\n--- Handling Get Leave Types Click ---")
    leave_types = leave_service.get_leave_types()
    if leave_types:
        print(f"UI: Found {len(leave_types)} leave types:")
        for lt in leave_types:
            print(f"  ID: {lt['id']}, Name: {lt['type_name']}, Default Balance: {lt.get('default_balance', 'N/A')}")
    else:
        print("UI: No leave types found or error retrieving them.")
    return leave_types

def handle_update_leave_balance_click(employee_id, leave_type_id, year, change_amount, is_initial_balance=False):
    """Simulates updating an employee's leave balance."""
    print(f"\n--- Handling Update Leave Balance Click (EmpID: {employee_id}, LTID: {leave_type_id}, Year: {year}) ---")
    new_balance = leave_service.update_leave_balance(employee_id, leave_type_id, year, change_amount, is_initial_balance)
    print(f"UI: Leave balance update processed. EmpID {employee_id}, LTID {leave_type_id}, Year {year}. New Balance: {new_balance}")
    return new_balance

def handle_view_leave_balance_click(employee_id, leave_type_id, year):
    """Simulates viewing an employee's leave balance."""
    print(f"\n--- Handling View Leave Balance Click (EmpID: {employee_id}, LTID: {leave_type_id}, Year: {year}) ---")
    balance = leave_service.get_leave_balance(employee_id, leave_type_id, year)
    print(f"UI: Leave balance for EmpID {employee_id}, LTID {leave_type_id}, Year {year}: {balance}")
    return balance

def handle_apply_leave_click(employee_id, leave_type_id, start_date_str, end_date_str, reason):
    """Simulates an employee applying for leave."""
    print(f"\n--- Handling Apply Leave Click (EmpID: {employee_id}, LTID: {leave_type_id}) ---")
    print(f"UI Params: Start: {start_date_str}, End: {end_date_str}, Reason: {reason}")
    
    # Basic validation for date strings (YYYY-MM-DD) in a real UI, here we assume they are correct or service handles it
    request_id = leave_service.apply_for_leave(employee_id, leave_type_id, start_date_str, end_date_str, reason)
    if request_id:
        print(f"UI: Leave request submitted. Request ID: {request_id}")
    else:
        print(f"UI: Failed to submit leave request for EmpID {employee_id}.")
    return request_id

def handle_approve_leave_click(leave_request_id, approver_id):
    """Simulates an approver approving a leave request."""
    print(f"\n--- Handling Approve Leave Click (ReqID: {leave_request_id}, ApproverID: {approver_id}) ---")
    success = leave_service.approve_leave_request(leave_request_id, approver_id)
    if success:
        print(f"UI: Leave request {leave_request_id} approved by {approver_id}.")
    else:
        print(f"UI: Failed to approve leave request {leave_request_id}.")
    return success

def handle_reject_leave_click(leave_request_id, approver_id):
    """Simulates an approver rejecting a leave request."""
    print(f"\n--- Handling Reject Leave Click (ReqID: {leave_request_id}, ApproverID: {approver_id}) ---")
    success = leave_service.reject_leave_request(leave_request_id, approver_id)
    if success:
        print(f"UI: Leave request {leave_request_id} rejected by {approver_id}.")
    else:
        print(f"UI: Failed to reject leave request {leave_request_id}.")
    return success

def handle_view_leave_requests_click(employee_id=None, status=None):
    """Simulates viewing leave requests with optional filters."""
    print("\n--- Handling View Leave Requests Click ---")
    print(f"UI Params: EmployeeID: {employee_id}, Status: {status}")
    requests = leave_service.get_leave_requests(employee_id=employee_id, status=status)
    if requests:
        print(f"UI: Found {len(requests)} leave requests:")
        for req in requests:
            print(f"  ID: {req['id']}, Emp: {req.get('employee_name', req['employee_id'])}, Type: {req.get('leave_type_name', req['leave_type_id'])}, "
                  f"Dates: {req['start_date']} to {req['end_date']}, Status: {req['status']}, Approver: {req.get('approver_username', req.get('approver_id', 'N/A'))}")
    elif not requests and requests is not None: # Empty list
        print("UI: No leave requests found matching criteria.")
    else: # None returned
        print("UI: Error retrieving leave requests.")
    return requests


if __name__ == '__main__':
    print("Leave View Module - Placeholder UI Handlers (Direct Demonstration)")
    db_file = os.path.join(PROJECT_ROOT, "dawami_app", "database", "dawami_dev.db")
    if not os.path.exists(db_file):
        print(f"WARNING: Database file not found at {db_file}. Demo may fail.")
        print("Please run 'scripts/database_setup.py' and 'scripts/seed_data.py' first.")
        sys.exit(1)

    # Assuming employee ID 1 and user ID 1 (as approver) exist from seed_data.py
    TEST_EMP_ID = 1
    TEST_APPROVER_USER_ID = 1 
    current_year = datetime.now().year

    # 1. Add Leave Types
    lt_annual_id = handle_add_leave_type_click("Annual Holiday", 22)
    lt_sick_id = handle_add_leave_type_click("Sick Day", 12)
    handle_get_leave_types_click()

    if not lt_annual_id or not lt_sick_id:
        print("\nCritical error: Could not create leave types for demo. Exiting.")
        # Attempt to get existing ones if creation failed due to already existing
        lts = leave_service.get_leave_types()
        for lt_item in lts:
            if lt_item['type_name'] == "Annual Holiday": lt_annual_id = lt_item['id']
            if lt_item['type_name'] == "Sick Day": lt_sick_id = lt_item['id']
        if not lt_annual_id or not lt_sick_id:
             print("Still couldn't get leave type IDs. Aborting demo.")
             sys.exit(1)


    # 2. Set Initial Balances
    handle_update_leave_balance_click(TEST_EMP_ID, lt_annual_id, current_year, 22, is_initial_balance=True)
    handle_update_leave_balance_click(TEST_EMP_ID, lt_sick_id, current_year, 12, is_initial_balance=True)
    handle_view_leave_balance_click(TEST_EMP_ID, lt_annual_id, current_year)
    handle_view_leave_balance_click(TEST_EMP_ID, lt_sick_id, current_year)

    # 3. Apply for Leave
    req1_start = (datetime.now() + timedelta(days=30)).strftime(leave_service.DATE_FORMAT)
    req1_end = (datetime.now() + timedelta(days=34)).strftime(leave_service.DATE_FORMAT)
    req_id1 = handle_apply_leave_click(TEST_EMP_ID, lt_annual_id, req1_start, req1_end, "Summer vacation")

    req2_start = (datetime.now() + timedelta(days=60)).strftime(leave_service.DATE_FORMAT)
    req2_end = (datetime.now() + timedelta(days=61)).strftime(leave_service.DATE_FORMAT)
    req_id2 = handle_apply_leave_click(TEST_EMP_ID, lt_sick_id, req2_start, req2_end, "Flu")
    
    # 4. View Pending Requests
    handle_view_leave_requests_click(status='Pending')

    # 5. Approve one, Reject one
    if req_id1:
        handle_approve_leave_click(req_id1, TEST_APPROVER_USER_ID)
    if req_id2:
        handle_reject_leave_click(req_id2, TEST_APPROVER_USER_ID)

    # 6. View requests for the employee
    handle_view_leave_requests_click(employee_id=TEST_EMP_ID)
    
    # 7. Simulate balance deduction for approved leave (5 days for req_id1)
    #    In a real system, this might be part of approve_leave_request or a separate, audited process.
    if req_id1: # Assuming req_id1 was for 5 days (34-30 + 1)
        handle_update_leave_balance_click(TEST_EMP_ID, lt_annual_id, current_year, -5)
    handle_view_leave_balance_click(TEST_EMP_ID, lt_annual_id, current_year)

    print("\nLeave View Module Demonstration Complete.")
