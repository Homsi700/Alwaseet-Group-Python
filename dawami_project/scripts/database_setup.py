import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dawami_app", "database")
DB_NAME = "dawami_dev.db"
DB_FILE = os.path.join(DB_DIR, DB_NAME)

def create_connection(db_file_path):
    """Create a database connection to a SQLite database."""
    conn = None
    try:
        os.makedirs(os.path.dirname(db_file_path), exist_ok=True)
        conn = sqlite3.connect(db_file_path)
        print(f"SQLite version: {sqlite3.sqlite_version}")
        print(f"Successfully connected to database at {db_file_path}")
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables(conn):
    """Create tables in the SQLite database."""
    try:
        cursor = conn.cursor()

        # Roles Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT NOT NULL UNIQUE,
                description TEXT
            );
        """)
        print("Table 'Roles' created successfully or already exists.")

        # Permissions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permission_name TEXT NOT NULL UNIQUE,
                description TEXT
            );
        """)
        print("Table 'Permissions' created successfully or already exists.")

        # RolePermissions Table (Junction Table)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RolePermissions (
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES Roles (id) ON DELETE CASCADE,
                FOREIGN KEY (permission_id) REFERENCES Permissions (id) ON DELETE CASCADE
            );
        """)
        print("Table 'RolePermissions' created successfully or already exists.")

        # WorkSchedules Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS WorkSchedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_name TEXT NOT NULL UNIQUE,
                expected_start_time TEXT NOT NULL, -- Store as TEXT in HH:MM format
                expected_end_time TEXT NOT NULL,   -- Store as TEXT in HH:MM format
                grace_period_minutes INTEGER DEFAULT 0
            );
        """)
        print("Table 'WorkSchedules' created successfully or already exists.")

        # Employees Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                employee_code TEXT NOT NULL UNIQUE,
                department TEXT,
                email TEXT UNIQUE,
                phone_number TEXT,
                job_title TEXT,
                work_schedule_id INTEGER,
                profile_picture_path TEXT,
                FOREIGN KEY (work_schedule_id) REFERENCES WorkSchedules (id) ON DELETE SET NULL
            );
        """)
        print("Table 'Employees' created successfully or already exists.")

        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                employee_id INTEGER UNIQUE, -- Can be NULL if user is not an employee
                is_active BOOLEAN DEFAULT 1, -- 1 for True, 0 for False
                FOREIGN KEY (role_id) REFERENCES Roles (id) ON DELETE RESTRICT,
                FOREIGN KEY (employee_id) REFERENCES Employees (id) ON DELETE SET NULL
            );
        """)
        print("Table 'Users' created successfully or already exists.")

        # AttendanceLog Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AttendanceLog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                clock_in_time TEXT NOT NULL,  -- ISO8601 format: YYYY-MM-DD HH:MM:SS
                clock_out_time TEXT,          -- ISO8601 format: YYYY-MM-DD HH:MM:SS, nullable
                attendance_date TEXT NOT NULL, -- ISO8601 format: YYYY-MM-DD
                notes TEXT,
                source TEXT, -- e.g., 'manual', 'fingerprint_device', 'mobile_app'
                FOREIGN KEY (employee_id) REFERENCES Employees (id) ON DELETE CASCADE
            );
        """)
        print("Table 'AttendanceLog' created successfully or already exists.")

        # LeaveTypes Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS LeaveTypes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT NOT NULL UNIQUE,
                default_balance REAL -- Using REAL for numeric type, can be NULL
            );
        """)
        print("Table 'LeaveTypes' created successfully or already exists.")

        # LeaveRequests Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS LeaveRequests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                leave_type_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,    -- ISO8601 format: YYYY-MM-DD
                end_date TEXT NOT NULL,      -- ISO8601 format: YYYY-MM-DD
                reason TEXT,
                status TEXT DEFAULT 'Pending', -- e.g., 'Pending', 'Approved', 'Rejected', 'Cancelled'
                approver_id INTEGER,
                request_date TEXT NOT NULL, -- ISO8601 format: YYYY-MM-DD HH:MM:SS
                FOREIGN KEY (employee_id) REFERENCES Employees (id) ON DELETE CASCADE,
                FOREIGN KEY (leave_type_id) REFERENCES LeaveTypes (id) ON DELETE RESTRICT,
                FOREIGN KEY (approver_id) REFERENCES Users (id) ON DELETE SET NULL
            );
        """)
        print("Table 'LeaveRequests' created successfully or already exists.")

        # LeaveBalances Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS LeaveBalances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                leave_type_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                balance REAL NOT NULL,
                UNIQUE (employee_id, leave_type_id, year),
                FOREIGN KEY (employee_id) REFERENCES Employees (id) ON DELETE CASCADE,
                FOREIGN KEY (leave_type_id) REFERENCES LeaveTypes (id) ON DELETE CASCADE
            );
        """)
        print("Table 'LeaveBalances' created successfully or already exists.")

        # Branches Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Branches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_name TEXT NOT NULL UNIQUE,
                location TEXT,
                branch_manager_id INTEGER,
                FOREIGN KEY (branch_manager_id) REFERENCES Employees (id) ON DELETE SET NULL
            );
        """)
        print("Table 'Branches' created successfully or already exists.")

        # SystemSettings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SystemSettings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT NOT NULL UNIQUE,
                setting_value TEXT,
                description TEXT
            );
        """)
        print("Table 'SystemSettings' created successfully or already exists.")

        # Holidays Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL UNIQUE, -- Format YYYY-MM-DD
                description TEXT -- Optional description
            );
        """)
        print("Table 'Holidays' created successfully or already exists.")

        conn.commit()
        print("All tables created successfully and changes committed.")

    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
        if conn:
            conn.rollback() # Rollback changes if any error occurs
            print("Changes rolled back.")


if __name__ == "__main__":
    # Ensure the database directory exists
    if not os.path.exists(DB_DIR):
        try:
            os.makedirs(DB_DIR)
            print(f"Database directory created at {DB_DIR}")
        except OSError as e:
            print(f"Error creating database directory {DB_DIR}: {e}")
            exit(1) # Exit if directory creation fails

    conn = create_connection(DB_FILE)

    if conn is not None:
        create_tables(conn)
        conn.close()
        print("Database connection closed.")
    else:
        print("Error! Cannot create the database connection.")
