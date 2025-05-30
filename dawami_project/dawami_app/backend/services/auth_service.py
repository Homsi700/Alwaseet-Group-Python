import hashlib
import sqlite3
import os

# Database path configuration
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

def get_db_connection():
    """Creates and returns a database connection."""
    os.makedirs(DB_DIR, exist_ok=True) # Ensure directory exists
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Access columns by name
    return conn

def hash_password(password):
    """Hashes a plain password using SHA256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(plain_password, hashed_password):
    """Verifies if the plain password matches the hashed one."""
    return hash_password(plain_password) == hashed_password

def _ensure_roles_exist(conn):
    """Ensures default roles (Admin, Manager, Employee) exist."""
    cursor = conn.cursor()
    default_roles = [
        ('Admin', 'Administrator with full system access.'),
        ('Manager', 'Manager with supervisory privileges.'),
        ('Employee', 'Regular employee with standard access.')
    ]
    for role_name, description in default_roles:
        cursor.execute("SELECT id FROM Roles WHERE role_name = ?", (role_name,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Roles (role_name, description) VALUES (?, ?)", (role_name, description))
    conn.commit()

def create_user(username, password, role_name, employee_id=None):
    """Creates a new user in the database."""
    conn = get_db_connection()
    try:
        _ensure_roles_exist(conn) # Ensure default roles are present

        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Roles WHERE role_name = ?", (role_name,))
        role_row = cursor.fetchone()
        if not role_row:
            print(f"Error: Role '{role_name}' not found.")
            return None
        role_id = role_row['id']

        hashed_pass = hash_password(password)
        
        cursor.execute("""
            INSERT INTO Users (username, password_hash, role_id, employee_id, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (username, hashed_pass, role_id, employee_id, True))
        conn.commit()
        user_id = cursor.lastrowid
        print(f"User '{username}' created successfully with ID: {user_id}")
        return {'id': user_id, 'username': username, 'role_id': role_id, 'employee_id': employee_id}
    except sqlite3.IntegrityError as e:
        print(f"Error creating user '{username}': {e}") # Likely username or employee_id already exists
        return None
    except sqlite3.Error as e:
        print(f"Database error while creating user '{username}': {e}")
        return None
    finally:
        if conn:
            conn.close()

def authenticate_user(username, password):
    """Authenticates a user by username and password."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, role_id, is_active FROM Users WHERE username = ?", (username,))
        user_row = cursor.fetchone()

        if user_row:
            if not user_row['is_active']:
                print(f"User '{username}' is not active.")
                return None
            
            if verify_password(password, user_row['password_hash']):
                print(f"User '{username}' authenticated successfully.")
                return {
                    'user_id': user_row['id'], 
                    'username': user_row['username'], 
                    'role_id': user_row['role_id']
                }
            else:
                print(f"Invalid password for user '{username}'.")
                return None
        else:
            print(f"User '{username}' not found.")
            return None
    except sqlite3.Error as e:
        print(f"Database error during authentication for user '{username}': {e}")
        return None
    finally:
        if conn:
            conn.close()

# --- RBAC Placeholder Functions ---
def get_user_permissions(user_id):
    """
    Placeholder for RBAC: Retrieves a list of permissions for a user.
    This will eventually query RolePermissions and Permissions tables.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Get user's role_id
        cursor.execute("SELECT role_id FROM Users WHERE id = ?", (user_id,))
        user_role_row = cursor.fetchone()
        if not user_role_row:
            return []
        
        role_id = user_role_row['role_id']

        # Get role_name (for hardcoded logic for now)
        cursor.execute("SELECT role_name FROM Roles WHERE id = ?", (role_id,))
        role_name_row = cursor.fetchone()
        if not role_name_row:
            return []
        role_name = role_name_row['role_name']

        # Get permissions based on role_name (hardcoded for now)
        # In a real implementation, this would join Users, Roles, RolePermissions, and Permissions
        cursor.execute("""
            SELECT p.permission_name
            FROM Permissions p
            JOIN RolePermissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = ?
        """, (role_id,))
        
        permissions = [row['permission_name'] for row in cursor.fetchall()]
        if not permissions: # Fallback to simple hardcoded if DB seeding isn't complete
            if role_name == 'Admin':
                return ['manage_users', 'view_reports', 'submit_leave_request', 'approve_leave_request', 'manage_settings', 'record_attendance_manual']
            elif role_name == 'Manager':
                return ['view_reports', 'approve_leave_request', 'record_attendance_manual']
            elif role_name == 'Employee':
                return ['submit_leave_request', 'record_attendance_manual']
        return permissions
        
    except sqlite3.Error as e:
        print(f"Database error in get_user_permissions: {e}")
        return []
    finally:
        if conn:
            conn.close()


def user_has_permission(user_id, permission_name_to_check):
    """
    Placeholder for RBAC: Checks if a user has a specific permission.
    """
    user_permissions_list = get_user_permissions(user_id)
    return permission_name_to_check in user_permissions_list

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    print("Auth Service Module - Direct Execution (for testing)")

    # Test password hashing
    sample_password = "testpassword123"
    hashed_sample_password = hash_password(sample_password)
    print(f"Plain: {sample_password}, Hashed: {hashed_sample_password}")
    print(f"Verification (correct): {verify_password(sample_password, hashed_sample_password)}")
    print(f"Verification (incorrect): {verify_password('wrongpassword', hashed_sample_password)}")

    # Note: User creation and authentication tests would ideally require a clean DB or mock.
    # For now, these are better tested via seed_data.py and the main application flow.
    # Example:
    # create_user("testuser", "testpass", "Employee")
    # authenticated_user = authenticate_user("testuser", "testpass")
    # if authenticated_user:
    #     print(f"Authenticated user: {authenticated_user}")
    #     permissions = get_user_permissions(authenticated_user['user_id'])
    #     print(f"User permissions: {permissions}")
    #     print(f"Has 'submit_leave_request' permission: {user_has_permission(authenticated_user['user_id'], 'submit_leave_request')}")
    #     print(f"Has 'manage_users' permission: {user_has_permission(authenticated_user['user_id'], 'manage_users')}")

    # Ensure DB directory exists for direct testing if needed
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        print(f"Database directory created at {DB_DIR} for direct testing.")
    
    # Test role creation (idempotent)
    conn_test = get_db_connection()
    _ensure_roles_exist(conn_test)
    print("Default roles ensured for direct testing.")
    conn_test.close()
