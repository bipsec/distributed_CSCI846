"""Graphical User Interface (GUI) client for the Course Registration System.

This module provides a Tkinter-based interface for users to interact with the
distributed database system via the Name Server and Database Server.
"""

import tkinter as tk
from tkinter import messagebox
import socket
import argparse
from typing import Optional

class CourseRegistrationApp:
    """Tkinter application for Course Registration.

    Handles connection, authentication, and interactions with the database server.
    
    Attributes:
        root (tk.Tk): The root Tkinter window.
        ns_host (str): Name Server Host IP.
        ns_port (int): Name Server Port.
        sock (Optional[socket.socket]): The socket connected to the database server.
        student_id (Optional[str]): The ID of the currently logged-in student.
    """

    def __init__(self, root: tk.Tk, ns_host: str, ns_port: int):
        """Initializes the application window and connects to the server.

        Args:
            root: The root Tkinter window.
            ns_host: Name Server Host IP.
            ns_port: Name Server Port.
        """
        self.root = root
        self.ns_host = ns_host
        self.ns_port = ns_port
        self.root.title("Course Registration System")
        self.root.geometry("600x400")
        
        self.sock: Optional[socket.socket] = None
        self.student_id: Optional[str] = None
        
        self.connect_to_server()
        if self.sock:
            self.show_login_screen()

    def connect_to_server(self) -> None:
        """Connects to the database server via Name Server lookup.

        Queries the Name Server for an available database server and establishes
        a TCP connection. Handles failures by showing an error message.
        """
        try:
            # Lookup DB Server
            ns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ns_sock.connect((self.ns_host, self.ns_port))
            ns_sock.sendall("LOOKUP".encode('utf-8'))
            response = ns_sock.recv(1024).decode('utf-8')
            ns_sock.close()
            
            parts = response.split()
            if parts[0] == "SUCCESS":
                server_host = parts[1]
                server_port = int(parts[2])
                
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((server_host, server_port))
            else:
                 messagebox.showerror("Connection Error", f"Name Server lookup failed: {response}")
                 self.root.destroy()
                 return

        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect: {e}")
            self.root.destroy()

    def send_request(self, command: str) -> str:
        """Sends a request to the server and returns the response.

        Args:
            command: The text command to send.

        Returns:
            The server's response as a string, or an error message.
        """
        if not self.sock:
            return "ERROR No connection"
        try:
            self.sock.sendall(command.encode('utf-8'))
            response = self.sock.recv(4096).decode('utf-8')
            return response
        except Exception as e:
            return f"ERROR {e}"

    def clear_screen(self) -> None:
        """Removes all widgets from the current window."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_screen(self) -> None:
        """Displays the login screen."""
        self.clear_screen()
        
        frame = tk.Frame(self.root)
        frame.pack(expand=True)
        
        tk.Label(frame, text="Student Login", font=("Arial", 16)).pack(pady=10)
        
        tk.Label(frame, text="Student ID:").pack()
        self.entry_id = tk.Entry(frame)
        self.entry_id.pack(pady=5)
        
        tk.Button(frame, text="Login", command=self.login).pack(pady=10)

    def login(self) -> None:
        """Handles the login process when the button is clicked."""
        student_id = self.entry_id.get().strip()
        if not student_id:
            messagebox.showwarning("Input Error", "Please enter a Student ID")
            return
            
        response = self.send_request(f"LOGIN {student_id}")
        if response.startswith("SUCCESS"):
            self.student_id = student_id
            self.show_dashboard()
        else:
            messagebox.showerror("Login Failed", response)

    def show_dashboard(self) -> None:
        """Displays the main dashboard with available and enrolled courses."""
        self.clear_screen()
        
        # Header
        header_frame = tk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(header_frame, text=f"Welcome, {self.student_id}", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        tk.Button(header_frame, text="Logout", command=self.logout).pack(side=tk.RIGHT)

        # Main Content
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Split into two columns
        left_frame = tk.LabelFrame(content_frame, text="Available Courses")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        right_frame = tk.LabelFrame(content_frame, text="My Courses")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Available Courses List
        self.courses_listbox = tk.Listbox(left_frame)
        self.courses_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tk.Button(left_frame, text="Register Selected", command=self.register_course).pack(pady=5)

        # My Courses List
        self.my_courses_listbox = tk.Listbox(right_frame)
        self.my_courses_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tk.Button(right_frame, text="Drop Selected", command=self.drop_course).pack(pady=5)

        # Refresh
        tk.Button(self.root, text="Refresh Data", command=self.refresh_data).pack(pady=5)
        
        self.refresh_data()

    def refresh_data(self) -> None:
        """Fetches latest data from server and updates the UI lists."""
        # Fetch Available
        resp = self.send_request("LIST")
        self.courses_listbox.delete(0, tk.END)
        if resp.startswith("SUCCESS"):
            lines = resp.split('\n')[1:] # Skip SUCCESS line
            for line in lines:
                if line.strip():
                    self.courses_listbox.insert(tk.END, line)

        # Fetch My Courses
        resp = self.send_request("MY_COURSES")
        self.my_courses_listbox.delete(0, tk.END)
        if resp.startswith("SUCCESS"):
            # Format: SUCCESS CS101, MATH201
            courses_str = resp[8:].strip()
            if courses_str:
                for c in courses_str.split(','):
                    self.my_courses_listbox.insert(tk.END, c.strip())

    def register_course(self) -> None:
        """Registers the user for the selected course."""
        selection = self.courses_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection", "Please select a course to register.")
            return
            
        course_str = self.courses_listbox.get(selection[0])
        # Extract ID (assuming format "ID: Name ...")
        course_id = course_str.split(':')[0]
        
        resp = self.send_request(f"REGISTER {course_id}")
        messagebox.showinfo("Result", resp)
        self.refresh_data()

    def drop_course(self) -> None:
        """Drops the user from the selected course."""
        selection = self.my_courses_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection", "Please select a course to drop.")
            return
            
        course_id = self.my_courses_listbox.get(selection[0])
        
        resp = self.send_request(f"DROP {course_id}")
        messagebox.showinfo("Result", resp)
        self.refresh_data()

    def logout(self) -> None:
        """Logs out the current user and returns to login screen."""
        self.student_id = None
        self.show_login_screen()

    def on_close(self) -> None:
        """Cleanly closes the connection and the application."""
        if self.sock:
            try:
                self.sock.sendall("EXIT".encode('utf-8'))
                self.sock.close()
            except:
                pass
        self.root.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed Course Registration GUI Client")
    parser.add_argument('--ns-host', type=str, default='127.0.0.1', help='Name Server Host (default: 127.0.0.1)')
    parser.add_argument('--ns-port', type=int, default=9090, help='Name Server Port (default: 9090)')
    
    args = parser.parse_args()

    root = tk.Tk()
    app = CourseRegistrationApp(root, args.ns_host, args.ns_port)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
