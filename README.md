# Distributed Course Registration System

A client-server distributed database system for course registration using Python socket programming. Contains a Name Server for service discovery and supports multi-user concurrent access.

## Features

- **Distributed Architecture**: Clients discover the Database Server via a Name Server.
- **Centralized Database Server**: Manages course data and student registrations with thread-safety.
- **Multiple Clients**: Supports multiple simultaneous connections.
- **Modular Codebase**: Organized into clear modules with comprehensive documentation.
- **Data Persistence**: Stores course and student data in JSON files within the `data/` directory.
- **Two Client Interfaces**:
  - **CLI Client**: Text-based command-line interface.
  - **GUI Client**: User-friendly graphical interface using Tkinter.

## Requirements

- Python 3.x
- `tkinter` (usually included with Python)
  - **Linux Users**: If `ModuleNotFoundError` occurs: `sudo apt-get install python3-tk`

## Project Structure

```text
Project/
├── src/
│   ├── common/         # Shared resources (Database)
│   ├── server/         # Database Server logic
│   ├── client/         # Client applications (CLI & GUI)
│   └── nameserver/     # Name Server logic
├── data/               # Persistent JSON data
├── tests/              # Integration tests
└── README.md
```

## How to Run

All commands must be executed from the project root directory.

### 1. Start the Name Server
The Name Server acts as a directory service. It must run first.
```bash
python3 -m src.nameserver.main --host 0.0.0.0
```
*Listens on `0.0.0.0:9090` by default. Use `--port` to change port.*
*Note the IP address of this machine (e.g., `192.168.1.5`).*

### 2. Start the Database Server
The Database Server registers itself with the Name Server upon startup.
```bash
python3 -m src.server.main --ns-host <NAME_SERVER_IP>
```
*Example: `python3 -m src.server.main --ns-host 192.168.1.5`*
*If running on the same machine, defaults to `127.0.0.1`.*

### 3. Start Clients
You can run multiple instances of clients.

**GUI Client (Recommended)**
```bash
python3 -m src.client.gui --ns-host <NAME_SERVER_IP>
```

**CLI Client**
```bash
python3 -m src.client.cli --ns-host <NAME_SERVER_IP>
```

## Running on Multiple Machines

To run the system across different computers on the same network:

1.  **Machine A (Name Server)**:
    Run `python3 -m src.nameserver.main --host 0.0.0.0`.
    Find Machine A's LAN IP (e.g., `192.168.1.5`).

2.  **Machine B (Database Server)**:
    Run `python3 -m src.server.main --host 0.0.0.0 --ns-host 192.168.1.5`.
    *The server will automatically detect its own LAN IP to register with the Name Server.*

3.  **Machine C (Client)**:
    Run `python3 -m src.client.gui --ns-host 192.168.1.5`.

## Usage

1. **Login**: Enter any Student ID (e.g., "Student1").
2. **Dashboard**: View "Available Courses" and "My Courses".
3. **Register**: Select an available course and click "Register".
4. **Drop**: Select a registered course and click "Drop".
5. **Refresh**: Update the lists to see changes made by other users.

