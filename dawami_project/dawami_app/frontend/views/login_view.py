import customtkinter as ctk
import os
import sys

# Add project root to sys.path to allow importing auth_service
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(PROJECT_ROOT)

from dawami_app.backend.services import auth_service

class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_login_success_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.on_login_success_callback = on_login_success_callback
        self.current_user = None # To store logged-in user info

        self.master.title("Dawami - Login")
        # Center the window
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = 350
        window_height = 300
        x_coord = (screen_width / 2) - (window_width / 2)
        y_coord = (screen_height / 2) - (window_height / 2)
        self.master.geometry(f"{window_width}x{window_height}+{int(x_coord)}+{int(y_coord)}")
        self.master.resizable(False, False)


        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # Allow message label to expand if needed

        ctk.CTkLabel(self, text="Dawami Login", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20, sticky="n")

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username", width=200)
        self.username_entry.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=200)
        self.password_entry.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.login_button = ctk.CTkButton(self, text="Login", command=self.handle_login, width=200)
        self.login_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.master.bind('<Return>', self.handle_login) # Bind Enter key to login

        self.message_label = ctk.CTkLabel(self, text="", text_color="red") # Red for errors, green for success
        self.message_label.grid(row=4, column=0, padx=20, pady=(5,10), sticky="ew")
        
        self.pack(expand=True, fill="both")


    def handle_login(self, event=None): # event parameter for <Return> key binding
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            self.message_label.configure(text="Username and password are required.", text_color="red")
            return

        user = auth_service.authenticate_user(username, password)

        if user:
            self.current_user = user
            success_message = f"Login successful! Welcome {user['username']}.\nRole ID: {user['role_id']}"
            self.message_label.configure(text=success_message, text_color="green")
            print(success_message)
            
            # Example of using RBAC (conceptual for now)
            permissions = auth_service.get_user_permissions(user['user_id'])
            print(f"User Permissions for {user['username']}: {permissions}")
            if auth_service.user_has_permission(user['user_id'], 'manage_users'):
                print(f"{user['username']} has 'manage_users' permission.")
            else:
                print(f"{user['username']} does NOT have 'manage_users' permission.")


            if self.on_login_success_callback:
                self.on_login_success_callback(user) # Pass user info to callback
        else:
            self.message_label.configure(text="Invalid username or password.", text_color="red")
            print("Login failed: Invalid credentials or inactive user.")
            self.current_user = None


def main_app_window(user_info):
    """Placeholder for the main application window after login."""
    app_root = ctk.CTk()
    app_root.title("Dawami - Main Application")
    screen_width = app_root.winfo_screenwidth()
    screen_height = app_root.winfo_screenheight()
    app_root.geometry(f"{screen_width//2}x{screen_height//2}")
    
    label = ctk.CTkLabel(app_root, text=f"Welcome, {user_info['username']}!\nYour Role ID is {user_info['role_id']}", font=("Arial", 20))
    label.pack(pady=20, padx=20)
    
    permissions = auth_service.get_user_permissions(user_info['user_id'])
    perms_label = ctk.CTkLabel(app_root, text=f"Your Permissions: {', '.join(permissions)}", font=("Arial", 12))
    perms_label.pack(pady=10)

    app_root.mainloop()


if __name__ == '__main__':
    # This part is for testing LoginView independently.
    # In the main application, LoginView will be integrated into main.py.
    root = ctk.CTk()
    
    def on_login(user):
        print(f"Login successful for user: {user['username']}. Transitioning to main app...")
        root.destroy() # Close the login window
        main_app_window(user) # Open the main application window

    login_frame = LoginView(master=root, on_login_success_callback=on_login)
    login_frame.pack(expand=True, fill="both")
    root.mainloop()

```
