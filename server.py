import socket
import threading
import json
from database import Database

HOST = '127.0.0.1'
PORT = 8080

db = Database()

def handle_client(client_socket):
    student_id = None
    try:
        while True:
            request = client_socket.recv(1024).decode('utf-8')
            if not request:
                break
            
            # Simple protocol: COMMAND JSON_ARGS
            # e.g., "LOGIN Student1"
            # e.g., "REGISTER CS101"
            
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
                # Format list nicely or send JSON? Let's send JSON for client to format, 
                # or just a pre-formatted string for simplicity as per "simple" req.
                # Let's send a string representation.
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

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server listening on {HOST}:{PORT}")

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
