"""Integration test for the distributed system.

Tests the full flow from Name Server lookup to Database interactions.
"""

import socket
import time
import subprocess
import sys
import os

def test_client_flow(student_id: str) -> list:
    """Runs a sequence of client operations.

    Args:
        student_id: The ID of the student to simulate.

    Returns:
        A list of result strings for verification.
    """
    results = []
    
    # 1. Name Server Lookup
    NAME_SERVER_HOST = '127.0.0.1'
    NAME_SERVER_PORT = 9090
    db_host = None
    db_port = None

    try:
        ns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ns_sock.connect((NAME_SERVER_HOST, NAME_SERVER_PORT))
        ns_sock.sendall("LOOKUP".encode('utf-8'))
        response = ns_sock.recv(1024).decode('utf-8')
        ns_sock.close()
        
        parts = response.split()
        if parts[0] == "SUCCESS":
            db_host = parts[1]
            db_port = int(parts[2])
            results.append(f"LOOKUP: Success -> {db_host}:{db_port}")
        else:
            results.append(f"LOOKUP: Failed -> {response}")
            return results
            
    except Exception as e:
        results.append(f"LOOKUP ERROR: {e}")
        return results

    if not db_host:
        return results

    # 2. DB Interactions
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((db_host, db_port))
        
        # Login
        sock.sendall(f"LOGIN {student_id}".encode('utf-8'))
        resp = sock.recv(4096).decode('utf-8')
        results.append(f"LOGIN: {resp.strip()}")

        # List
        sock.sendall("LIST".encode('utf-8'))
        resp = sock.recv(4096).decode('utf-8')
        results.append(f"LIST: {resp.strip()[:20]}...")

        sock.sendall("EXIT".encode('utf-8'))
        sock.close()
    except Exception as e:
        results.append(f"DB ERROR: {e}")
    
    return results

def main():
    """Main verification block."""
    # Ensure current directory is in python path
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    print("Starting Name Server (binding to 127.0.0.1)...")
    ns_process = subprocess.Popen(
        [sys.executable, "-m", "src.nameserver.main", "--host", "127.0.0.1", "--port", "9090"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    time.sleep(2) # Wait for startup

    print("Starting DB Server (connecting to NS at 127.0.0.1)...")
    db_process = subprocess.Popen(
        [sys.executable, "-m", "src.server.main", "--host", "127.0.0.1", "--port", "8080", "--ns-host", "127.0.0.1", "--ns-port", "9090"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    time.sleep(2) # Wait for startup and registration

    try:
        print("Running Client Test...")
        # Client uses default 127.0.0.1 if not specified, but let's be explicit to test args
        # Since test_client_flow calls python code directly, we can't easily pass args to it unless we change it 
        # or just rely on default being 127.0.0.1 inside the function.
        # But wait, test_client_flow manually does socket stuff. It mimics a client.
        # So we just need to make sure the SERVERS are up and running with the new args.
        # The test_client_flow function itself creates a socket to 127.0.0.1:9090.
        
        res = test_client_flow("TestStudentNS")
        for r in res:
            print(r)
    finally:
        print("Terminating servers...")
        ns_process.terminate()
        db_process.terminate()
        # Ensure they are dead
        ns_process.wait()
        db_process.wait()
        print("Done.")

if __name__ == "__main__":
    main()
