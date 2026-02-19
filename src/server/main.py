"""Main entry point for the distributed database server.

This module initializes the server socket, registers tables with the Name Server,
and handles incoming client connections using threads.
"""

import socket
import threading
import argparse
import json
import os
from typing import Optional, Dict

# Import Database from the common module
try:
    from src.common.database import Database
except ImportError:
    # Fallback if running directly from within src/server (for testing)
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    from src.common.database import Database

# Initialize Database
db = Database()

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

def get_lan_ip() -> str:
    """Attempts to determine the machine's LAN IP address.

    Connects to an external public IP (Google DNS) to see which local interface is used.
    Does not actually send data.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def handle_client(client_socket: socket.socket) -> None:
    """Handles communication with a connected client.

    Supports PUT, GET, and DEL commands for key-value tables.
    Runs in a dedicated thread for each client.

    Args:
        client_socket: The socket object for the connected client.
    """
    try:
        while True:
            request = client_socket.recv(1024).decode('utf-8')
            if not request:
                break
            
            parts = request.strip().split(' ')
            command = parts[0].upper() if parts else ""

            response = "ERROR Invalid command"

            if command == 'PUT':
                put_parts = request.strip().split(' ', 3)
                if len(put_parts) >= 4:
                    table_name = put_parts[1]
                    key = put_parts[2]
                    value = put_parts[3]
                    success, msg = db.put(table_name, key, value)
                    response = f"SUCCESS: ({table_name}, {key}) {msg}"
                else:
                    response = "ERROR Usage: PUT <table> <key> <data>"

            elif command == 'GET':
                get_parts = request.strip().split(' ', 2)
                if len(get_parts) >= 3:
                    table_name = get_parts[1]
                    key = get_parts[2]
                    success, msg = db.get(table_name, key)
                    response = f"RESULT: {msg}" if success else f"ERROR: {msg}"
                else:
                    response = "ERROR Usage: GET <table> <key>"

            elif command == 'DEL':
                del_parts = request.strip().split(' ', 2)
                if len(del_parts) >= 3:
                    table_name = del_parts[1]
                    key = del_parts[2]
                    success, msg = db.delete(table_name, key)
                    response = f"SUCCESS: ({table_name}, {key}) {msg}" if success else f"ERROR: {msg}"
                else:
                    response = "ERROR Usage: DEL <table> <key>"

            elif command == 'EXIT':
                break

            client_socket.sendall(response.encode('utf-8'))
    
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        print("Connection closed")
        client_socket.close()

def register_with_name_server(host: str, port: int, ns_host: str, ns_port: int, tables: list) -> None:
    """Registers this server's tables with the Name Server.

    Connects to the Name Server and sends table -> host/port mappings.
    If 'host' is 0.0.0.0, it attempts to resolve the actual LAN IP.

    Args:
        host: The host this server is bound to.
        port: The port this server is bound to.
        ns_host: The IP of the Name Server.
        ns_port: The port of the Name Server.
        tables: List of table names hosted by this server.
    """
    
    # If we are binding to all interfaces (0.0.0.0), we need to tell the Name Server
    # our actual IP so clients can reach us.
    register_host = host
    if host == '0.0.0.0':
        register_host = get_lan_ip()
        print(f"Binding to 0.0.0.0, detected LAN IP as {register_host}")

    try:
        for table_name in tables:
            ns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ns_sock.connect((ns_host, ns_port))

            msg = f"REGISTER {table_name} {register_host} {port}"
            ns_sock.sendall(msg.encode('utf-8'))

            response = ns_sock.recv(1024).decode('utf-8')
            if response == "SUCCESS":
                print(f"Registered table '{table_name}' with Name Server at {ns_host}:{ns_port}")
            else:
                print(f"Failed to register table '{table_name}': {response}")
            ns_sock.close()
    except Exception as e:
        print(f"Could not connect to Name Server at {ns_host}:{ns_port}: {e}")

def start_server(host: str, port: int, ns_host: str, ns_port: int, tables: list) -> None:
    """Starts the Database Server.

    Binds to HOST and PORT, registers tables with Name Server, and accepts incoming connections.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((host, port))
    except OSError as e:
        print(f"Failed to bind to {host}:{port}: {e}")
        return

    server.listen(5)
    print(f"Server listening on {host}:{port}")
    
    # Register with Name Server
    register_with_name_server(host, port, ns_host, ns_port, tables)

    try:
        while True:
            client_sock, addr = server.accept()
            print(f"Accepted connection from {addr}")
            client_handler = threading.Thread(target=handle_client, args=(client_sock,))
            client_handler.start()
    except KeyboardInterrupt:
        print("Server stopping...")
    finally:
        server.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed Key-Value Database Server")
    parser.add_argument('--config', type=str, default='config.json', help='Path to JSON config file')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host interface to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on (default: 8080)')
    parser.add_argument('--ns-host', type=str, default='127.0.0.1', help='Name Server Host (default: 127.0.0.1)')
    parser.add_argument('--ns-port', type=int, default=9090, help='Name Server Port (default: 9090)')
    parser.add_argument('--tables', type=str, default='default', help='Comma-separated table names')

    config_args, _ = parser.parse_known_args()
    config = load_config(config_args.config)
    server_config = config.get('server', {}) if isinstance(config, dict) else {}
    parser.set_defaults(
        host=server_config.get('host', parser.get_default('host')),
        port=server_config.get('port', parser.get_default('port')),
        ns_host=server_config.get('ns_host', parser.get_default('ns_host')),
        ns_port=server_config.get('ns_port', parser.get_default('ns_port')),
        tables=server_config.get('tables', parser.get_default('tables')),
    )

    args = parser.parse_args()
    tables = [t.strip() for t in args.tables.split(',') if t.strip()]
    start_server(args.host, args.port, args.ns_host, args.ns_port, tables)
