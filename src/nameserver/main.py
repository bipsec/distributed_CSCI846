import socket
import threading
import argparse
from typing import List, Tuple

# Store list of active servers as (host, port)
active_servers: List[Tuple[str, int]] = []

def handle_client(client_socket: socket.socket) -> None:
    """Handles requests from clients and servers.

    Supports the following commands:
    - REGISTER <HOST> <PORT>: Adds a server to the active list.
    - LOOKUP: Returns the address of an available server.

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
            if len(parts) >= 3:
                server_host = parts[1]
                server_port = int(parts[2])
                if (server_host, server_port) not in active_servers:
                    active_servers.append((server_host, server_port))
                    print(f"Registered server: {server_host}:{server_port}")
                response = "SUCCESS"
            else:
                response = "ERROR Usage: REGISTER <HOST> <PORT>"
        
        elif command == 'LOOKUP':
            if active_servers:
                # Simple round-robin or first available
                # For now, just return the first one
                host, port = active_servers[0]
                response = f"SUCCESS {host} {port}"
            else:
                response = "ERROR No servers available"
        
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
    parser = argparse.ArgumentParser(description="Distributed Course Registration Name Server")
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host interface to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=9090, help='Port to listen on (default: 9090)')
    
    args = parser.parse_args()
    start_name_server(args.host, args.port)
