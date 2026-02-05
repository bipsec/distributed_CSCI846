"""Main entry point for the distributed database server.

This module initializes the server socket, registers with the Name Server,
and handles incoming client connections using threads.
"""

import socket
import threading
from typing import Optional

# Import Database from the common module
# Adjust path assuming this is run as a module or with PYTHONPATH set appropriately
try:
    from src.common.database import Database
except ImportError:
    # Fallback if running directly from within src/server (for testing)
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    from src.common.database import Database

HOST = '127.0.0.1'
PORT = 8080

# Initialize Database
db = Database()

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

def register_with_name_server() -> None:
    """Registers this server with the Name Server.

    Connects to the Name Server on localhost:9090 and sends its own host/port.
    Prints status to stdout.
    """
    NAME_SERVER_HOST = '127.0.0.1'
    NAME_SERVER_PORT = 9090
    try:
        ns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ns_sock.connect((NAME_SERVER_HOST, NAME_SERVER_PORT))
        msg = f"REGISTER {HOST} {PORT}"
        ns_sock.sendall(msg.encode('utf-8'))
        response = ns_sock.recv(1024).decode('utf-8')
        if response == "SUCCESS":
            print(f"Successfully registered with Name Server at {NAME_SERVER_HOST}:{NAME_SERVER_PORT}")
        else:
            print(f"Failed to register with Name Server: {response}")
        ns_sock.close()
    except Exception as e:
        print(f"Could not connect to Name Server: {e}")

def start_server() -> None:
    """Starts the Database Server.

    Binds to HOST and PORT, registers with Name Server, and accepts incoming connections.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server listening on {HOST}:{PORT}")
    
    # Register with Name Server
    register_with_name_server()

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
    start_server()
