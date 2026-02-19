"""Course Registration Service Layer.

Provides high-level course registration operations on top of the key-value database.
Handles validation, transactions, and business logic.
"""

import socket
import json
from typing import Tuple, Optional, Dict, List

class RegistrationService:
    """Manages course registration operations using the distributed key-value system."""

    def __init__(self, ns_host: str, ns_port: int):
        """Initialize the service with Name Server details.

        Args:
            ns_host: Name Server host IP.
            ns_port: Name Server port.
        """
        self.ns_host = ns_host
        self.ns_port = ns_port

    def lookup_server(self, table_name: str) -> Tuple[Optional[str], Optional[int]]:
        """Resolve a table to its server address via Name Server."""
        try:
            ns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ns_sock.connect((self.ns_host, self.ns_port))
            ns_sock.sendall(f"LOOKUP {table_name}".encode('utf-8'))
            response = ns_sock.recv(1024).decode('utf-8')
            ns_sock.close()

            parts = response.split()
            if parts and parts[0] == "SUCCESS" and len(parts) >= 3:
                return parts[1], int(parts[2])
            return None, None
        except Exception:
            return None, None

    def send_command(self, table: str, command: str) -> Tuple[bool, str]:
        """Send a command to the database server for a table."""
        host, port = self.lookup_server(table)
        if not host or not port:
            return False, "Table not found"

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.sendall(command.encode('utf-8'))
            response = sock.recv(4096).decode('utf-8')
            sock.sendall("EXIT".encode('utf-8'))
            sock.close()
            return True, response
        except Exception as e:
            return False, str(e)

    def get_courses(self) -> Tuple[bool, Dict[str, Dict]]:
        """Retrieve all available courses."""
        host, port = self.lookup_server("Courses")
        if not host or not port:
            return False, {}

        try:
            courses = {}
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            
            # Get all course keys by trying common course IDs or listing
            # For now, fetch a predefined set of courses
            course_ids = ["CS101", "MATH201", "PHY301", "ENG101"]
            
            for course_id in course_ids:
                sock.sendall(f"GET Courses {course_id}".encode('utf-8'))
                response = sock.recv(4096).decode('utf-8')
                
                if response.startswith("RESULT:"):
                    try:
                        data = json.loads(response[7:].strip())
                        courses[course_id] = data
                    except json.JSONDecodeError:
                        pass
            
            sock.sendall("EXIT".encode('utf-8'))
            sock.close()
            return True, courses
        except Exception as e:
            return False, {}

    def register_student(self, student_id: str, course_id: str) -> Tuple[bool, str]:
        """Register a student for a course."""
        # 1. Get course info
        success, response = self.send_command("Courses", f"GET Courses {course_id}")
        if not success or "ERROR" in response:
            return False, "Course not found"

        try:
            # Parse course data
            if response.startswith("RESULT:"):
                course_data = json.loads(response[7:].strip())
            else:
                return False, "Invalid course data"

            # 2. Check capacity
            enrolled = course_data.get("enrolled", 0)
            capacity = course_data.get("capacity", 30)
            if enrolled >= capacity:
                return False, "Course full"

            # 3. Check if already enrolled
            success, response = self.send_command("Students", f"GET Students {student_id}")
            if success and "RESULT:" in response:
                try:
                    student_data = json.loads(response[7:].strip())
                    enrollments = student_data.get("enrollments", [])
                    if course_id in enrollments:
                        return False, "Already registered"
                except json.JSONDecodeError:
                    enrollments = []
            else:
                enrollments = []

            # 4. Update course (increment enrolled)
            new_enrolled = enrolled + 1
            course_data["enrolled"] = new_enrolled
            success, _ = self.send_command("Courses", f"PUT Courses {course_id} {json.dumps(course_data)}")
            if not success:
                return False, "Failed to update course"

            # 5. Update student (add to enrollments)
            enrollments.append(course_id)
            student_data = {"enrollments": enrollments}
            success, _ = self.send_command("Students", f"PUT Students {student_id} {json.dumps(student_data)}")
            if not success:
                return False, "Failed to update student enrollment"

            return True, "Registration successful"
        except Exception as e:
            return False, str(e)

    def drop_course(self, student_id: str, course_id: str) -> Tuple[bool, str]:
        """Drop a student from a course."""
        # 1. Get student info
        success, response = self.send_command("Students", f"GET Students {student_id}")
        if not success or "ERROR" in response:
            return False, "Student not found"

        try:
            if response.startswith("RESULT:"):
                student_data = json.loads(response[7:].strip())
            else:
                return False, "Invalid student data"

            enrollments = student_data.get("enrollments", [])
            if course_id not in enrollments:
                return False, "Not registered for this course"

            # 2. Get course info
            success, response = self.send_command("Courses", f"GET Courses {course_id}")
            if not success or "ERROR" in response:
                return False, "Course not found"

            if response.startswith("RESULT:"):
                course_data = json.loads(response[7:].strip())
            else:
                return False, "Invalid course data"

            # 3. Update course (decrement enrolled)
            enrolled = course_data.get("enrolled", 1)
            new_enrolled = max(0, enrolled - 1)
            course_data["enrolled"] = new_enrolled
            success, _ = self.send_command("Courses", f"PUT Courses {course_id} {json.dumps(course_data)}")
            if not success:
                return False, "Failed to update course"

            # 4. Update student (remove from enrollments)
            enrollments.remove(course_id)
            student_data["enrollments"] = enrollments
            success, _ = self.send_command("Students", f"PUT Students {student_id} {json.dumps(student_data)}")
            if not success:
                return False, "Failed to update student"

            return True, "Course dropped"
        except Exception as e:
            return False, str(e)

    def get_student_courses(self, student_id: str) -> Tuple[bool, List[str]]:
        """Get list of courses a student is enrolled in."""
        success, response = self.send_command("Students", f"GET Students {student_id}")
        if not success or "ERROR" in response:
            return False, []

        try:
            if response.startswith("RESULT:"):
                student_data = json.loads(response[7:].strip())
                enrollments = student_data.get("enrollments", [])
                return True, enrollments
            return False, []
        except json.JSONDecodeError:
            return False, []

    def initialize_courses(self) -> bool:
        """Initialize sample courses in the database."""
        courses = {
            "CS101": {"name": "Introduction to CS", "capacity": 30, "enrolled": 0},
            "MATH201": {"name": "Calculus I", "capacity": 25, "enrolled": 0},
            "PHY301": {"name": "Physics III", "capacity": 20, "enrolled": 0},
            "ENG101": {"name": "English Composition", "capacity": 15, "enrolled": 0},
        }

        for course_id, course_data in courses.items():
            success, _ = self.send_command("Courses", f"PUT Courses {course_id} {json.dumps(course_data)}")
            if not success:
                return False
        return True
