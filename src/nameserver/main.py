import socket
import threading
import argparse
import json
import os
from typing import Dict, Tuple

# Store mapping of table name -> (host, port)
table_registry: Dict[str, Tuple[str, int]] = {}

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

def handle_client(client_socket: socket.socket) -> None:
    """Handles requests from clients and servers.

    Supports the following commands:
    - REGISTER <TABLE> <HOST> <PORT>: Registers a table with a server address.
    - LOOKUP <TABLE>: Returns the server address for a table.

    Args:
        client_socket: The socket object for the connected client/server.
    """
    try:
        request = client_socket.recv(1024).decode('utf-8')
        if not request:
            return

        parts = request.strip().split()
        command = parts[0].upper()

        response = "ERROR Invalid Command"

        if command == 'REGISTER':
            if len(parts) >= 4:
                table_name = parts[1]
                server_host = parts[2]
                server_port = int(parts[3])
                table_registry[table_name] = (server_host, server_port)
                print(f"Registered table '{table_name}' -> {server_host}:{server_port}")
                response = "SUCCESS"
            else:
                response = "ERROR Usage: REGISTER <TABLE> <HOST> <PORT>"

        elif command == 'LOOKUP':
            if len(parts) >= 2:
                table_name = parts[1]
                if table_name in table_registry:
                    host, port = table_registry[table_name]
                    response = f"SUCCESS {host} {port}"
                else:
                    response = "ERROR Table not found"
            else:
                response = "ERROR Usage: LOOKUP <TABLE>"
        
        client_socket.sendall(response.encode('utf-8'))

    except Exception as e:
        print(f"Error handling request: {e}")
    finally:
        client_socket.close()

def start_name_server(host: str, port: int) -> None:
    """Starts the Name Server.

    Binds to HOST and PORT and listens for incoming connections.
    
    Args:
        host: The interface to bind to.
        port: The port to listen on.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Name Server listening on {host}:{port}")

    try:
        while True:
            client_sock, addr = server.accept()
            # print(f"Accepted connection from {addr}")
            client_handler = threading.Thread(target=handle_client, args=(client_sock,))
            client_handler.start()
    except KeyboardInterrupt:
        print("Name Server stopping...")
    finally:
        server.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed Key-Value Name Server")
    parser.add_argument('--config', type=str, default='config.json', help='Path to JSON config file')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host interface to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=9090, help='Port to listen on (default: 9090)')

    config_args, _ = parser.parse_known_args()
    config = load_config(config_args.config)
    ns_config = config.get('name_server', {}) if isinstance(config, dict) else {}
    parser.set_defaults(
        host=ns_config.get('host', parser.get_default('host')),
        port=ns_config.get('port', parser.get_default('port')),
    )

    args = parser.parse_args()
    start_name_server(args.host, args.port)
