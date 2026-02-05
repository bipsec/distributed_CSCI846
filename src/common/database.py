"""Database module for the distributed course registration system.

This module handles persistent storage of course and student data using JSON files.
It provides thread-safe access to the data.
"""

import json
import os
import threading
from typing import Dict, List, Tuple, Any

class Database:
    """Manages course and student data with thread-safe operations.

    Attributes:
        courses_file (str): Path to the courses JSON file.
        students_file (str): Path to the students JSON file.
        lock (threading.Lock): Mutex for thread-safe access.
        courses (Dict): In-memory cache of course data.
        students (Dict): In-memory cache of student registration data.
    """

    def __init__(self, courses_file: str = 'data/courses.json', students_file: str = 'data/students.json'):
        """Initializes the Database with file paths and loads data.

        Args:
            courses_file: Path to the JSON file storing course information.
                Defaults to 'data/courses.json'.
            students_file: Path to the JSON file storing student registrations.
                Defaults to 'data/students.json'.
        """
        self.courses_file = courses_file
        self.students_file = students_file
        self.lock = threading.Lock()
        self._load_data()

    def _load_data(self) -> None:
        """Loads data from JSON files into memory.

        Creates empty files if they do not exist.
        """
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.courses_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.students_file), exist_ok=True)

        if not os.path.exists(self.courses_file):
            self.courses = {}
            self._save_courses()
        else:
            with open(self.courses_file, 'r') as f:
                self.courses = json.load(f)

        if not os.path.exists(self.students_file):
            self.students = {}
            self._save_students()
        else:
            with open(self.students_file, 'r') as f:
                self.students = json.load(f)

    def _save_courses(self) -> None:
        """Saves current course data to the JSON file."""
        with open(self.courses_file, 'w') as f:
            json.dump(self.courses, f, indent=4)

    def _save_students(self) -> None:
        """Saves current student data to the JSON file."""
        with open(self.students_file, 'w') as f:
            json.dump(self.students, f, indent=4)

    def get_courses(self) -> Dict[str, Any]:
        """Retrieves all available courses.

        Returns:
            A dictionary of courses where keys are course IDs and values are details.
        """
        with self.lock:
            return self.courses

    def get_student_courses(self, student_id: str) -> List[str]:
        """Retrieves the list of courses a student is registered for.

        Args:
            student_id: The ID of the student.

        Returns:
            A list of course IDs the student is enrolled in.
        """
        with self.lock:
            return self.students.get(student_id, [])

    def register_student(self, student_id: str, course_id: str) -> Tuple[bool, str]:
        """Registers a student for a specific course.

        Args:
            student_id: The ID of the student.
            course_id: The ID of the course to register for.

        Returns:
            A tuple (success, message), where success is a boolean indicating
            if the operation was successful, and message is a string description.
        """
        with self.lock:
            if course_id not in self.courses:
                return False, "Course not found."
            
            course = self.courses[course_id]
            if course['enrolled'] >= course['capacity']:
                return False, "Course full."

            if student_id not in self.students:
                self.students[student_id] = []

            if course_id in self.students[student_id]:
                return False, "Already registered."

            # Update state
            self.courses[course_id]['enrolled'] += 1
            self.students[student_id].append(course_id)
            
            self._save_courses()
            self._save_students()
            return True, "Registration successful."

    def drop_course(self, student_id: str, course_id: str) -> Tuple[bool, str]:
        """Drops a course for a student.

        Args:
            student_id: The ID of the student.
            course_id: The ID of the course to drop.

        Returns:
            A tuple (success, message) indicating the result of the operation.
        """
        with self.lock:
            if student_id not in self.students or course_id not in self.students[student_id]:
                return False, "Not registered for this course."

            if course_id in self.courses:
                 self.courses[course_id]['enrolled'] -= 1

            self.students[student_id].remove(course_id)
            
            self._save_courses()
            self._save_students()
            return True, "Course dropped."
