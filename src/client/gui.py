"""Graphical User Interface (GUI) client for the key-value database system.

This module provides a Tkinter-based interface for users to interact with the
distributed database system via the Name Server and Database Server.
"""

import tkinter as tk
from tkinter import messagebox
import socket
import argparse
import json
import os
from typing import Optional, Dict, Tuple

class KeyValueClientApp:
    """Tkinter application for key-value operations.

    Resolves table locations via the Name Server and sends PUT/GET/DEL commands.
    """

    def __init__(self, root: tk.Tk, ns_host: str, ns_port: int):
        """Initializes the application window.

        Args:
            root: The root Tkinter window.
            ns_host: Name Server Host IP.
            ns_port: Name Server Port.
        """
        self.root = root
        self.ns_host = ns_host
        self.ns_port = ns_port
        self.root.title("Distributed Key-Value Client")
        self.root.geometry("640x420")

        self._build_ui()

    def lookup_server(self, table_name: str) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        """Resolves the server for a table via the Name Server."""
        try:
            ns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ns_sock.connect((self.ns_host, self.ns_port))
            ns_sock.sendall(f"LOOKUP {table_name}".encode('utf-8'))
            response = ns_sock.recv(1024).decode('utf-8')
            ns_sock.close()

            parts = response.split()
            if parts and parts[0] == "SUCCESS" and len(parts) >= 3:
                return parts[1], int(parts[2]), None
            return None, None, response
        except Exception as e:
            return None, None, str(e)

    def send_request(self, table_name: str, command: str) -> str:
        """Resolves the table and sends a request to the server."""
        host, port, error = self.lookup_server(table_name)
        if not host or not port:
            return f"ERROR: {error or 'Table not found'}"

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.sendall(command.encode('utf-8'))
            response = sock.recv(4096).decode('utf-8')
            sock.sendall("EXIT".encode('utf-8'))
            sock.close()
            return response
        except Exception as e:
            return f"ERROR: {e}"

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, padx=12, pady=12)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(container, text="Table").grid(row=0, column=0, sticky="w")
        self.table_entry = tk.Entry(container, width=30)
        self.table_entry.grid(row=0, column=1, sticky="ew", pady=4)

        tk.Label(container, text="Key").grid(row=1, column=0, sticky="w")
        self.key_entry = tk.Entry(container, width=30)
        self.key_entry.grid(row=1, column=1, sticky="ew", pady=4)

        tk.Label(container, text="Data").grid(row=2, column=0, sticky="w")
        self.data_entry = tk.Entry(container, width=30)
        self.data_entry.grid(row=2, column=1, sticky="ew", pady=4)

        button_frame = tk.Frame(container)
        button_frame.grid(row=3, column=0, columnspan=2, pady=8)
        tk.Button(button_frame, text="PUT", width=10, command=self.handle_put).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="GET", width=10, command=self.handle_get).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="DEL", width=10, command=self.handle_del).pack(side=tk.LEFT, padx=4)

        tk.Label(container, text="Response").grid(row=4, column=0, sticky="w")
        self.response_text = tk.Text(container, height=8, wrap=tk.WORD)
        self.response_text.grid(row=5, column=0, columnspan=2, sticky="nsew")

        container.columnconfigure(1, weight=1)
        container.rowconfigure(5, weight=1)

    def _get_inputs(self) -> Tuple[str, str, str]:
        return (
            self.table_entry.get().strip(),
            self.key_entry.get().strip(),
            self.data_entry.get().strip(),
        )

    def _set_response(self, message: str) -> None:
        self.response_text.delete("1.0", tk.END)
        self.response_text.insert(tk.END, message)

    def handle_put(self) -> None:
        table, key, data = self._get_inputs()
        if not table or not key or not data:
            messagebox.showwarning("Input Error", "Table, key, and data are required for PUT.")
            return
        response = self.send_request(table, f"PUT {table} {key} {data}")
        self._set_response(response)

    def handle_get(self) -> None:
        table, key, _ = self._get_inputs()
        if not table or not key:
            messagebox.showwarning("Input Error", "Table and key are required for GET.")
            return
        response = self.send_request(table, f"GET {table} {key}")
        self._set_response(response)

    def handle_del(self) -> None:
        table, key, _ = self._get_inputs()
        if not table or not key:
            messagebox.showwarning("Input Error", "Table and key are required for DEL.")
            return
        response = self.send_request(table, f"DEL {table} {key}")
        self._set_response(response)

    def on_close(self) -> None:
        """Cleanly closes the connection and the application."""
        self.root.destroy()

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed Key-Value GUI Client")
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
    app = KeyValueClientApp(root, resolved_ns_host, args.ns_port)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
