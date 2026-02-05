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
python3 -m src.nameserver.main
```
*Listens on `127.0.0.1:9090`*

### 2. Start the Database Server
The Database Server registers itself with the Name Server upon startup.
```bash
python3 -m src.server.main
```
*Listens on `127.0.0.1:8080`*

### 3. Start Clients
You can run multiple instances of clients.

**GUI Client (Recommended)**
```bash
python3 -m src.client.gui
```

**CLI Client**
```bash
python3 -m src.client.cli
```

## Usage

1. **Login**: Enter any Student ID (e.g., "Student1").
2. **Dashboard**: View "Available Courses" and "My Courses".
3. **Register**: Select an available course and click "Register".
4. **Drop**: Select a registered course and click "Drop".
5. **Refresh**: Update the lists to see changes made by other users.

