"""Graphical User Interface (GUI) for Course Registration System.

Built on top of the distributed key-value database using Tkinter.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import socket
import argparse
import json
import os
from typing import Dict
from src.registration.service import RegistrationService

def load_config(path: str) -> Dict[str, Dict[str, object]]:
    """Loads JSON config if it exists, otherwise returns empty config."""
    if not path:
        return {}
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

def resolve_hostname(hostname: str, hostname_map: Dict[str, str] = None) -> str:
    """Resolves a hostname or IP address to an IP address.
    
    Checks local hostname mapping in config first, then tries DNS resolution.
    
    Args:
        hostname: Hostname (e.g., 'Ali') or IP address.
        hostname_map: Optional dictionary mapping hostnames to IP addresses.
        
    Returns:
        Resolved IP address string, or the original input if resolution fails.
    """
    # Check local hostname mapping first
    if hostname_map and hostname in hostname_map:
        ip = hostname_map[hostname]
        print(f"Resolved '{hostname}' to {ip} (from config)")
        return ip
    
    # Try DNS resolution
    try:
        ip = socket.gethostbyname(hostname)
        print(f"Resolved '{hostname}' to {ip} (from DNS)")
        return ip
    except socket.gaierror:
        print(f"Warning: Could not resolve hostname '{hostname}', using as-is")
        return hostname

class CourseRegistrationApp:
    """Tkinter GUI application for course registration."""

    def __init__(self, root: tk.Tk, ns_host: str, ns_port: int):
        """Initialize the application."""
        self.root = root
        self.service = RegistrationService(ns_host, ns_port)
        self.current_student = None
        
        self.root.title("Course Registration System")
        self.root.geometry("700x500")
        
        # Initialize courses
        self.service.initialize_courses()
        
        self.show_login_screen()

    def clear_widgets(self) -> None:
        """Clear all widgets from the window."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_screen(self) -> None:
        """Display the login screen."""
        self.clear_widgets()
        
        frame = tk.Frame(self.root)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(frame, text="Course Registration System", font=("Arial", 18, "bold")).pack(pady=20)
        
        tk.Label(frame, text="Student ID:", font=("Arial", 12)).pack(pady=10)
        self.login_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.login_entry.pack(pady=5)
        self.login_entry.focus()
        
        tk.Button(frame, text="Login", command=self.handle_login, font=("Arial", 12), width=20).pack(pady=15)

    def handle_login(self) -> None:
        """Handle login action."""
        student_id = self.login_entry.get().strip()
        if not student_id:
            messagebox.showwarning("Input Error", "Please enter a Student ID")
            return
        
        self.current_student = student_id
        self.show_dashboard()

    def show_dashboard(self) -> None:
        """Display the main dashboard."""
        self.clear_widgets()
        
        # Header frame
        header = tk.Frame(self.root, bg="#2c3e50")
        header.pack(fill=tk.X, padx=0, pady=0)
        
        tk.Label(header, text=f"Welcome, {self.current_student}", font=("Arial", 14, "bold"), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=20, pady=10)
        tk.Button(header, text="Logout", command=self.handle_logout, bg="#e74c3c", fg="white", font=("Arial", 10)).pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Main content
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left side: Available Courses
        left_frame = tk.LabelFrame(main_frame, text="Available Courses", font=("Arial", 11, "bold"))
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        scrollbar_left = tk.Scrollbar(left_frame)
        scrollbar_left.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.courses_listbox = tk.Listbox(left_frame, yscrollcommand=scrollbar_left.set, font=("Arial", 10))
        self.courses_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar_left.config(command=self.courses_listbox.yview)
        
        tk.Button(left_frame, text="Register Selected", command=self.handle_register, font=("Arial", 10), bg="#27ae60", fg="white").pack(pady=5, padx=5, fill=tk.X)
        
        # Right side: My Courses
        right_frame = tk.LabelFrame(main_frame, text="My Courses", font=("Arial", 11, "bold"))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        scrollbar_right = tk.Scrollbar(right_frame)
        scrollbar_right.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.my_courses_listbox = tk.Listbox(right_frame, yscrollcommand=scrollbar_right.set, font=("Arial", 10))
        self.my_courses_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar_right.config(command=self.my_courses_listbox.yview)
        
        tk.Button(right_frame, text="Drop Selected", command=self.handle_drop, font=("Arial", 10), bg="#e74c3c", fg="white").pack(pady=5, padx=5, fill=tk.X)
        
        # Refresh button
        tk.Button(self.root, text="Refresh Data", command=self.refresh_data, font=("Arial", 10), bg="#3498db", fg="white").pack(pady=10, padx=15, fill=tk.X)
        
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh course lists."""
        # Fetch available courses
        self.courses_listbox.delete(0, tk.END)
        success, courses = self.service.get_courses()
        if success and courses:
            for course_id, course_info in courses.items():
                name = course_info.get("name", "Unknown")
                capacity = course_info.get("capacity", 0)
                enrolled = course_info.get("enrolled", 0)
                self.courses_listbox.insert(tk.END, f"{course_id}: {name} ({enrolled}/{capacity})")
        
        # Fetch my courses
        self.my_courses_listbox.delete(0, tk.END)
        success, my_courses = self.service.get_student_courses(self.current_student)
        if success and my_courses:
            for course_id in my_courses:
                self.my_courses_listbox.insert(tk.END, course_id)

    def handle_register(self) -> None:
        """Handle course registration."""
        selection = self.courses_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a course to register.")
            return
        
        course_str = self.courses_listbox.get(selection[0])
        course_id = course_str.split(':')[0].strip()
        
        success, msg = self.service.register_student(self.current_student, course_id)
        if success:
            messagebox.showinfo("Success", msg)
            self.refresh_data()
        else:
            messagebox.showerror("Error", msg)

    def handle_drop(self) -> None:
        """Handle course drop."""
        selection = self.my_courses_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a course to drop.")
            return
        
        course_id = self.my_courses_listbox.get(selection[0]).strip()
        
        success, msg = self.service.drop_course(self.current_student, course_id)
        if success:
            messagebox.showinfo("Success", msg)
            self.refresh_data()
        else:
            messagebox.showerror("Error", msg)

    def handle_logout(self) -> None:
        """Handle logout."""
        self.current_student = None
        self.show_login_screen()

    def on_close(self) -> None:
        """Handle window close."""
        self.root.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Course Registration System GUI")
    parser.add_argument('--config', type=str, default='config.json', help='Path to JSON config file')
    parser.add_argument('--ns-host', type=str, default='127.0.0.1', help='Name Server Host (default: 127.0.0.1)')
    parser.add_argument('--ns-port', type=int, default=9090, help='Name Server Port (default: 9090)')

    config_args, _ = parser.parse_known_args()
    config = load_config(config_args.config)
    client_config = config.get('client', {}) if isinstance(config, dict) else {}
    parser.set_defaults(
        ns_host=client_config.get('ns_host', parser.get_default('ns_host')),
        ns_port=client_config.get('ns_port', parser.get_default('ns_port')),
    )

    args = parser.parse_args()
    
    # Get hostname mapping from config
    hostname_map = config.get('hostname_map', {}) if isinstance(config, dict) else {}
    
    # Resolve hostname to IP address
    resolved_ns_host = resolve_hostname(args.ns_host, hostname_map)

    root = tk.Tk()
    app = CourseRegistrationApp(root, resolved_ns_host, args.ns_port)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
