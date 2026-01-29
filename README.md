# Distributed Course Registration System

A simple client-server distributed database system for course registration using Python socket programming.

## Features

- **Centralized Server**: Manages course data and student registrations accurately with thread-safe operations.
- **Multiple Clients**: Supports multiple students connecting simultaneously.
- **Data Persistence**: Stores course details and student records in JSON files.
- **Two Client Interfaces**:
  - **CLI Client**: A text-based command-line interface.
  - **GUI Client**: A user-friendly graphical interface using Tkinter.

## Requirements

- Python 3.x
- `tkinter` (usually included with Python)
  - **Linux Users**: If you get a `ModuleNotFoundError`, install it via:
    ```bash
    sudo apt-get install python3-tk
    ```

## How to Run

### 1. Start the Server
The server must be running for clients to connect.

```bash
python3 server.py
```
*The server will listen on `127.0.0.1:8080`.*

### 2. Start a Client
Open a new terminal window to run a client. You can run multiple instances to simulate multiple students.

**Option A: GUI Client (Recommended)**
```bash
python3 gui_client.py
```
- Enter a Student ID to login.
- Use the buttons to Register or Drop courses.
- Click "Refresh" to see updated availability.

**Option B: CLI Client**
```bash
python3 client.py
```
- Follow the on-screen menu prompts.

## Project Structure

- `server.py`: Main server application logic.
- `database.py`: Handles database operations (loading/saving JSON, thread safety).
- `client.py`: Command-line client application.
- `gui_client.py`: Graphical client application.
- `courses.json`: Database file for course information.
- `students.json`: Database file for student registrations (created automatically).
