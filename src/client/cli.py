"""Command Line Interface (CLI) client for the key-value database system.

This module provides a text-based interface for users to interact with the
distributed database system via the Name Server and Database Server.
"""

import socket
import argparse
import json
import os
from typing import Tuple, Optional, Dict

def get_server_address(ns_host: str, ns_port: int, table_name: str) -> Tuple[Optional[str], Optional[int]]:
    """Retrieves the Database Server address for a table from the Name Server.

    Args:
        ns_host: Name Server Host IP.
        ns_port: Name Server Port.
        table_name: Table to resolve.

    Returns:
        A tuple (host, port) if successful, or (None, None) if lookup fails.
    """
    try:
        ns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ns_sock.connect((ns_host, ns_port))
        ns_sock.sendall(f"LOOKUP {table_name}".encode('utf-8'))
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

def load_config(path: str) -> Dict[str, Dict[str, object]]:
    """Loads JSON config if it exists, otherwise returns empty config."""
    if not path:
        return {}
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

def main(ns_host: str, ns_port: int) -> None:
    """Main function to run the CLI client.

    Accepts PUT/GET/DEL commands and routes them to the correct server.
    """
    print("Distributed Key-Value Client")
    print("Commands: PUT <table> <key> <data> | GET <table> <key> | DEL <table> <key>")
    print("Type 'exit' to quit.")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break

        parts = line.split()
        command = parts[0].upper()

        if command == "PUT":
            if len(parts) < 4:
                print("ERROR: Usage: PUT <table> <key> <data>")
                continue
            table_name = parts[1]
            key = parts[2]
            data = " ".join(parts[3:])
            request = f"PUT {table_name} {key} {data}"
        elif command in ("GET", "DEL"):
            if len(parts) != 3:
                print(f"ERROR: Usage: {command} <table> <key>")
                continue
            table_name = parts[1]
            request = line
        else:
            print("ERROR: Unknown command")
            continue

        db_host, db_port = get_server_address(ns_host, ns_port, table_name)
        if not db_host:
            print("ERROR: Could not resolve table via Name Server")
            continue

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((db_host, db_port))
            sock.sendall(request.encode('utf-8'))
            response = sock.recv(4096).decode('utf-8')
            print(response)
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            try:
                sock.sendall("EXIT".encode('utf-8'))
                sock.close()
            except Exception:
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed Key-Value CLI Client")
    parser.add_argument('--config', type=str, default='config.json', help='Path to JSON config file')
    parser.add_argument('--ns-host', type=str, default='127.0.0.1', help='Name Server Host (default: 127.0.0.1)')
    parser.add_argument('--ns-port', type=int, default=9090, help='Name Server Port (default: 9090)')

    config_args, _ = parser.parse_known_args()
    config = load_config(config_args.config)
    client_config = config.get('client', {}) if isinstance(config, dict) else {}
    parser.set_defaults(
        ns_host=client_config.get('ns_host', parser.get_default('ns_host')),
        ns_port=client_config.get('ns_port', parser.get_default('ns_port')),
    )

    args = parser.parse_args()
    main(args.ns_host, args.ns_port)
