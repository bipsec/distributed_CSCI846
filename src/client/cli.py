"""Command Line Interface (CLI) client for the Course Registration System.

This module provides a text-based interface for users to interact with the
distributed database system via the Name Server and Database Server.
"""

import socket
import argparse
from typing import Tuple, Optional

def get_server_address(ns_host: str, ns_port: int) -> Tuple[Optional[str], Optional[int]]:
    """Retrieves the active Database Server address from the Name Server.

    Connects to the Name Server and requests a server address.
    
    Args:
        ns_host: Name Server Host IP.
        ns_port: Name Server Port.

    Returns:
        A tuple (host, port) if successful, or (None, None) if lookup fails.
    """
    try:
        ns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ns_sock.connect((ns_host, ns_port))
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
        print(f"Could not connect to Name Server at {ns_host}:{ns_port}: {e}")
        return None, None

def main(ns_host: str, ns_port: int) -> None:
    """Main function to run the CLI client.

    Connects to the server, prompts for login, and provides a menu for
    course registration operations.
    """
    db_host, db_port = get_server_address(ns_host, ns_port)
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
    parser = argparse.ArgumentParser(description="Distributed Course Registration CLI Client")
    parser.add_argument('--ns-host', type=str, default='127.0.0.1', help='Name Server Host (default: 127.0.0.1)')
    parser.add_argument('--ns-port', type=int, default=9090, help='Name Server Port (default: 9090)')
    
    args = parser.parse_args()
    main(args.ns_host, args.ns_port)
