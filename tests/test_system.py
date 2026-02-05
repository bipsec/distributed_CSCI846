import socket
import time
import threading

HOST = '127.0.0.1'
PORT = 8080

def send_command(command):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        sock.sendall(command.encode('utf-8'))
        
        # Keep connection open for multiple commands simulation 
        # But for this simple test function we might just want one interaction
        # Actually our server loop expects one connection per client session
        # So we should adapt this helper or just write a full test flow
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def test_client_flow(student_id):
    results = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        
        # 1. Login
        sock.sendall(f"LOGIN {student_id}".encode('utf-8'))
        resp = sock.recv(4096).decode('utf-8')
        results.append(f"LOGIN: {resp.strip()}")

        # 2. List
        sock.sendall("LIST".encode('utf-8'))
        resp = sock.recv(4096).decode('utf-8')
        results.append(f"LIST: {resp.strip()[:20]}...") # Truncate for brevity

        # 3. Register CS101
        sock.sendall("REGISTER CS101".encode('utf-8'))
        resp = sock.recv(4096).decode('utf-8')
        results.append(f"REGISTER CS101: {resp.strip()}")

        # 4. My Courses
        sock.sendall("MY_COURSES".encode('utf-8'))
        resp = sock.recv(4096).decode('utf-8')
        results.append(f"MY_COURSES: {resp.strip()}")
        
        # 5. Drop CS101
        sock.sendall("DROP CS101".encode('utf-8'))
        resp = sock.recv(4096).decode('utf-8')
        results.append(f"DROP CS101: {resp.strip()}")

        sock.sendall("EXIT".encode('utf-8'))
        sock.close()
    except Exception as e:
        results.append(f"ERROR: {e}")
    
    return results

if __name__ == "__main__":
    print("Starting Test...")
    res = test_client_flow("TestStudent1")
    for r in res:
        print(r)
    print("Test Complete.")
