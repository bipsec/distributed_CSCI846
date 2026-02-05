"""Command Line Interface (CLI) client for the Course Registration System.

This module provides a text-based interface for users to interact with the
distributed database system via the Name Server and Database Server.
"""

import socket
from typing import Tuple, Optional

def get_server_address() -> Tuple[Optional[str], Optional[int]]:
    """Retrieves the active Database Server address from the Name Server.

    Connects to the Name Server on localhost:9090 and requests a server address.

    Returns:
        A tuple (host, port) if successful, or (None, None) if lookup fails.
    """
    NAME_SERVER_HOST = '127.0.0.1'
    NAME_SERVER_PORT = 9090
    try:
        ns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ns_sock.connect((NAME_SERVER_HOST, NAME_SERVER_PORT))
        ns_sock.sendall("LOOKUP".encode('utf-8'))
        response = ns_sock.recv(1024).decode('utf-8')
        ns_sock.close()
        
        parts = response.split()
        if parts[0] == "SUCCESS":
            return parts[1], int(parts[2])
        else:
            print(f"Name Server lookup failed: {response}")
            return None, None
    except Exception as e:
        print(f"Could not connect to Name Server: {e}")
        return None, None

def main() -> None:
    """Main function to run the CLI client.

    Connects to the server, prompts for login, and provides a menu for
    course registration operations.
    """
    db_host, db_port = get_server_address()
    if not db_host:
        print("Could not retrieve database server address. Exiting.")
        return

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((db_host, db_port))
    except ConnectionRefusedError:
        print(f"Could not connect to server at {db_host}:{db_port}. Is it running?")
        return

    print(f"Connected to Course Registration System at {db_host}:{db_port}")
    
    current_student: Optional[str] = None

    try:
        while True:
            if not current_student:
                print("\n=== LOGIN ===")
                student_id = input("Enter Student ID to login (or 'quit' to exit): ").strip()
                if student_id.lower() == 'quit':
                    break
                
                sock.sendall(f"LOGIN {student_id}".encode('utf-8'))
                response = sock.recv(4096).decode('utf-8')
                print(response)
                
                if response.startswith("SUCCESS"):
                    current_student = student_id
            
            else:
                print(f"\n=== MENU ({current_student}) ===")
                print("1. List Courses")
                print("2. Register for Course")
                print("3. Drop Course")
                print("4. My Courses")
                print("5. Logout")
                print("6. Quit/Exit")
                
                choice = input("Select an option: ").strip()

                if choice == '1':
                    sock.sendall("LIST".encode('utf-8'))
                    response = sock.recv(4096).decode('utf-8')
                    # Format output, remove SUCCESS prefix if present for cleaner look
                    if response.startswith("SUCCESS"):
                        print(response[7:].strip())
                    else:
                        print(response)
                
                elif choice == '2':
                    cid = input("Enter Course ID: ").strip()
                    sock.sendall(f"REGISTER {cid}".encode('utf-8'))
                    print(sock.recv(4096).decode('utf-8'))

                elif choice == '3':
                    cid = input("Enter Course ID: ").strip()
                    sock.sendall(f"DROP {cid}".encode('utf-8'))
                    print(sock.recv(4096).decode('utf-8'))

                elif choice == '4':
                    sock.sendall("MY_COURSES".encode('utf-8'))
                    print(sock.recv(4096).decode('utf-8'))

                elif choice == '5':
                    current_student = None
                    print("Logged out.")

                elif choice == '6':
                    break
                
                else:
                    print("Invalid option.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.sendall("EXIT".encode('utf-8'))
        sock.close()
        print("Disconnected.")

if __name__ == "__main__":
    main()
