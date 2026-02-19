"""Command Line Interface (CLI) for Course Registration System.

Built on top of the distributed key-value database.
"""

import argparse
import json
import os
from typing import Dict
from src.registration.service import RegistrationService

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
    """Main function to run the registration CLI client."""
    service = RegistrationService(ns_host, ns_port)
    
    print("=" * 60)
    print("        Distributed Course Registration System")
    print("=" * 60)
    print("\nInitializing courses...")
    service.initialize_courses()
    print("Courses initialized.\n")

    current_student = None

    while True:
        if not current_student:
            print("\n" + "=" * 60)
            print("LOGIN")
            print("=" * 60)
            student_id = input("Enter Student ID (or 'quit' to exit): ").strip()
            
            if student_id.lower() == 'quit':
                break
            
            if not student_id:
                print("ERROR: Student ID cannot be empty")
                continue
            
            current_student = student_id
            print(f"SUCCESS: Logged in as {student_id}")
        
        else:
            print(f"\n" + "=" * 60)
            print(f"MENU - {current_student}")
            print("=" * 60)
            print("1. List Courses")
            print("2. Register for Course")
            print("3. Drop Course")
            print("4. My Courses")
            print("5. Logout")
            print("6. Exit")
            
            choice = input("\nSelect an option: ").strip()
            
            if choice == '1':
                print("\n--- Available Courses ---")
                success, courses = service.get_courses()
                if success and courses:
                    for course_id, course_info in courses.items():
                        name = course_info.get("name", "Unknown")
                        capacity = course_info.get("capacity", 0)
                        enrolled = course_info.get("enrolled", 0)
                        print(f"{course_id}: {name} ({enrolled}/{capacity})")
                else:
                    print("No courses available or error retrieving courses.")
            
            elif choice == '2':
                course_id = input("Enter Course ID to register: ").strip().upper()
                success, msg = service.register_student(current_student, course_id)
                if success:
                    print(f"SUCCESS: {msg}")
                else:
                    print(f"ERROR: {msg}")
            
            elif choice == '3':
                course_id = input("Enter Course ID to drop: ").strip().upper()
                success, msg = service.drop_course(current_student, course_id)
                if success:
                    print(f"SUCCESS: {msg}")
                else:
                    print(f"ERROR: {msg}")
            
            elif choice == '4':
                success, courses = service.get_student_courses(current_student)
                if success:
                    if courses:
                        print("\n--- My Courses ---")
                        for course_id in courses:
                            print(f"  - {course_id}")
                    else:
                        print("Not registered for any courses.")
                else:
                    print("ERROR: Could not retrieve your courses")
            
            elif choice == '5':
                current_student = None
                print("Logged out.")
            
            elif choice == '6':
                break
            
            else:
                print("ERROR: Invalid option, please try again.")

    print("\nThank you for using the Course Registration System!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Course Registration System CLI")
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
