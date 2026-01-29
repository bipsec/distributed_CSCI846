import socket

HOST = '127.0.0.1'
PORT = 8080

def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("Could not connect to server. Is it running?")
        return

    print("Connected to Course Registration System")
    
    current_student = None

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
