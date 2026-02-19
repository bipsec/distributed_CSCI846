# Distributed Course Registration System

A distributed key-value database system with a course registration application layer built on top.
Uses Python socket programming with a Name Server for DNS-style table resolution and supports multi-user concurrent access.

## Quick Start (Course Registration)

**Terminal 1:**  `python -m src.nameserver.main`

**Terminal 2:**  `python -m src.server.main --tables Courses,Students`

**Terminal 3:**  `python -m src.client.registration_gui`  or  `python -m src.client.registration_cli`

For raw key-value operations, use: `python -m src.client.gui` or `python -m src.client.cli` with `--tables Phone,Email`

## Architecture

**Two-Layer Design:**
1. **Core Distributed Key-Value Database** (Assignment Required):
   - Name Server: Maps table names to server locations (DNS-style)
   - Database Servers: Store key-value pairs persisted to JSON
   - Protocol: `PUT`, `GET`, `DEL` operations
   
2. **Course Registration Application** (Built on Top):
   - Registration Service: High-level business logic (register, drop, validate)
   - Registration CLI & GUI: User-friendly interfaces
   - Uses the key-value layer for persistence

## Features

- **Distributed Architecture**: Tables map to servers via Name Server (DNS-style)
- **Thread-Safe Database**: Concurrent client handling with mutual exclusion locks
- **Key-Value Storage**: Generic PUT/GET/DEL protocol for any table
- **Configuration File**: JSON config for easy deployment
- **Two Interface Sets**:
  - **Raw Key-Value Clients**: Direct database access (cli.py, gui.py)
  - **Course Registration Clients**: High-level registration app (registration_cli.py, registration_gui.py)
- **Multi-Server Support**: Tables can be distributed across multiple servers

## Requirements

- Python 3.x
- `tkinter` (usually included with Python)
  - **Linux Users**: If `ModuleNotFoundError` occurs: `sudo apt-get install python3-tk`

## Project Structure

```
Project/
├── src/
│   ├── common/              # Shared database implementation
│   ├── server/              # Database server (PUT/GET/DEL)
│   ├── nameserver/          # Name Server (table registry)
│   ├── client/
│   │   ├── cli.py           # Key-value CLI
│   │   ├── gui.py           # Key-value GUI
│   │   ├── registration_cli.py       # Course registration CLI
│   │   └── registration_gui.py       # Course registration GUI
│   └── registration/
│       └── service.py       # Registration business logic
├── data/                    # Persistent storage
├── config.json              # Configuration
└── README.md
```

## How to Run

All commands from project root.

### Option 1: Course Registration System (Recommended)

**Terminal 1:**
```bash
python -m src.nameserver.main
```

**Terminal 2:**
```bash
python -m src.server.main --tables Courses,Students
```

**Terminal 3 (GUI):**
```bash
python -m src.client.registration_gui
```

**OR Terminal 3 (CLI):**
```bash
python -m src.client.registration_cli
```

Use the CLI for these commands:
```
1. List Courses
2. Register for Course
3. Drop Course
4. My Courses
5. Logout
```

### Option 2: Raw Key-Value Database

**Terminal 1:**
```bash
python -m src.nameserver.main
```

**Terminal 2:**
```bash
python -m src.server.main --tables Phone,Email
```

**Terminal 3 (GUI):**
```bash
python -m src.client.gui
```

**OR Terminal 3 (CLI):**
```bash
python -m src.client.cli
```

Use the CLI for these commands:
```
PUT Phone Alan 701-111-2222
GET Phone Alan
DEL Phone Alan
exit
```

## Protocol

### Name Server
- `REGISTER <TABLE> <HOST> <PORT>` → Register a table with a server
- `LOOKUP <TABLE>` → Get server address for a table

### Database Server
- `PUT <table> <key> <data>` → Insert/update key-value pair
- `GET <table> <key>` → Retrieve value
- `DEL <table> <key>` → Delete a key
- `EXIT` → Close connection

## Running on Multiple Machines

Example: 3 machines on LAN

1. **Machine A (Name Server)**:
   ```bash
   python -m src.nameserver.main --host 0.0.0.0
   # Note: Machine A's IP is 192.168.1.5
   ```

2. **Machine B (Database Server)**:
   ```bash
   python -m src.server.main --ns-host 192.168.1.5 --tables Courses,Students
   ```

3. **Machine C (Client)**:
   ```bash
   python -m src.client.registration_gui --ns-host 192.168.1.5
   ```

## Configuration

Edit `config.json`:
```json
{
  "name_server": {
    "host": "0.0.0.0",
    "port": 9090
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "ns_host": "127.0.0.1",
    "ns_port": 9090,
    "tables": "Courses,Students"
  },
  "client": {
    "ns_host": "127.0.0.1",
    "ns_port": 9090
  }
}
```

CLI flags override config values.

## Usage

### Course Registration System
1. **Login**: Enter any Student ID (e.g., "Alice")
2. **View Courses**: See all available courses with enrollment stats
3. **Register**: Select a course and register (validates capacity, prevents duplicates)
4. **Drop**: Remove yourself from a course
5. **Refresh**: Update lists to see changes from other clients

### Key-Value System
```
PUT <table> <key> <data>    # Insert or update
GET <table> <key>           # Retrieve a value
DEL <table> <key>           # Delete a key
exit                        # Quit
```

## Design Notes

- **Atomicity**: Individual PUT/GET/DEL operations are atomic (protected by locks)
- **Tables**: Each table is independent; can be on different servers
- **Data Format**: Values are stored as JSON strings in the database
- **Persistence**: All data persisted to `data/tables.json`
- **Name Resolution**: DNS-style mapping of table names to server addresses
- **Course Registration Transactions**: Registration = update multiple tables atomically

