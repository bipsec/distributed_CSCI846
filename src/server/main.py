"""Main entry point for the distributed database server.

This module initializes the server socket, registers with the Name Server,
and handles incoming client connections using threads.
"""

import socket
import threading
import argparse
from typing import Optional

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

    Processes commands like LOGIN, LIST, REGISTER, etc., and sends back responses.
    Runs in a dedicated thread for each client.

    Args:
        client_socket: The socket object for the connected client.
    """
    student_id: Optional[str] = None
    try:
        while True:
            request = client_socket.recv(1024).decode('utf-8')
            if not request:
                break
            
            # Protocol: COMMAND ARGS
            parts = request.strip().split(' ', 1)
            command = parts[0].upper()
            arg = parts[1] if len(parts) > 1 else ""

            response = "ERROR Invalid command"

            if command == 'LOGIN':
                student_id = arg.strip()
                if student_id:
                    response = f"SUCCESS Welcome {student_id}"
                else:
                    response = "ERROR Missing student ID"
            
            elif command == 'LIST':
                courses = db.get_courses()
                # Create a formatted string for the client
                resp_lines = []
                for cid, cdata in courses.items():
                    resp_lines.append(f"{cid}: {cdata['name']} ({cdata['enrolled']}/{cdata['capacity']})")
                response = "SUCCESS\n" + "\n".join(resp_lines)

            elif command == 'REGISTER':
                if not student_id:
                    response = "ERROR Please login first"
                else:
                    course_id = arg.strip()
                    success, msg = db.register_student(student_id, course_id)
                    response = ("SUCCESS " if success else "ERROR ") + msg

            elif command == 'DROP':
                if not student_id:
                    response = "ERROR Please login first"
                else:
                    course_id = arg.strip()
                    success, msg = db.drop_course(student_id, course_id)
                    response = ("SUCCESS " if success else "ERROR ") + msg
            
            elif command == 'MY_COURSES':
                if not student_id:
                    response = "ERROR Please login first"
                else:
                    my_courses = db.get_student_courses(student_id)
                    response = "SUCCESS " + ", ".join(my_courses)

            elif command == 'EXIT':
                break

            client_socket.sendall(response.encode('utf-8'))
    
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        print(f"Connection closed for {student_id}")
        client_socket.close()

def register_with_name_server(host: str, port: int, ns_host: str, ns_port: int) -> None:
    """Registers this server with the Name Server.

    Connects to the Name Server and sends its own host/port.
    If 'host' is 0.0.0.0, it attempts to resolve the actual LAN IP.

    Args:
        host: The host this server is bound to.
        port: The port this server is bound to.
        ns_host: The IP of the Name Server.
        ns_port: The port of the Name Server.
    """
    
    # If we are binding to all interfaces (0.0.0.0), we need to tell the Name Server
    # our actual IP so clients can reach us.
    register_host = host
    if host == '0.0.0.0':
        register_host = get_lan_ip()
        print(f"Binding to 0.0.0.0, detected LAN IP as {register_host}")

    try:
        ns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ns_sock.connect((ns_host, ns_port))
        
        msg = f"REGISTER {register_host} {port}"
        ns_sock.sendall(msg.encode('utf-8'))
        
        response = ns_sock.recv(1024).decode('utf-8')
        if response == "SUCCESS":
            print(f"Successfully registered with Name Server at {ns_host}:{ns_port}")
        else:
            print(f"Failed to register with Name Server: {response}")
        ns_sock.close()
    except Exception as e:
        print(f"Could not connect to Name Server at {ns_host}:{ns_port}: {e}")

def start_server(host: str, port: int, ns_host: str, ns_port: int) -> None:
    """Starts the Database Server.

    Binds to HOST and PORT, registers with Name Server, and accepts incoming connections.
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
    register_with_name_server(host, port, ns_host, ns_port)

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
    parser = argparse.ArgumentParser(description="Distributed Course Registration Database Server")
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host interface to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on (default: 8080)')
    parser.add_argument('--ns-host', type=str, default='127.0.0.1', help='Name Server Host (default: 127.0.0.1)')
    parser.add_argument('--ns-port', type=int, default=9090, help='Name Server Port (default: 9090)')
    
    args = parser.parse_args()
    start_server(args.host, args.port, args.ns_host, args.ns_port)
