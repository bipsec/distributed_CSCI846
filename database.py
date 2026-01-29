import json
import os
import threading

class Database:
    def __init__(self, courses_file='courses.json', students_file='students.json'):
        self.courses_file = courses_file
        self.students_file = students_file
        self.lock = threading.Lock()
        self._load_data()

    def _load_data(self):
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

    def _save_courses(self):
        with open(self.courses_file, 'w') as f:
            json.dump(self.courses, f, indent=4)

    def _save_students(self):
        with open(self.students_file, 'w') as f:
            json.dump(self.students, f, indent=4)

    def get_courses(self):
        with self.lock:
            return self.courses

    def get_student_courses(self, student_id):
        with self.lock:
            return self.students.get(student_id, [])

    def register_student(self, student_id, course_id):
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

    def drop_course(self, student_id, course_id):
        with self.lock:
            if student_id not in self.students or course_id not in self.students[student_id]:
                return False, "Not registered for this course."

            if course_id in self.courses:
                 self.courses[course_id]['enrolled'] -= 1

            self.students[student_id].remove(course_id)
            
            self._save_courses()
            self._save_students()
            return True, "Course dropped."
