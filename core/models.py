from django.db import models
from django.contrib.auth.models import User

# --- 1. Course Model ---


class Course(models.Model):
    """Represents a course, managing config settings like marks."""
    course_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE)

    # Configuration for grading
    total_lectures_possible = models.IntegerField(default=12)

    def __str__(self):
        return f"{self.course_code} - {self.name}"

# --- 2. Student Model ---


class Student(models.Model):
    """Represents a student enrolled in a course."""
    index_number = models.CharField(
        max_length=15, unique=True, primary_key=True)
    full_name = models.CharField(max_length=150)
    courses = models.ManyToManyField(Course)

    def __str__(self):
        return f"{self.full_name} ({self.index_number})"

    # Auto Grading Logic (Calculates score based on attendance records)
    @property
    def attendance_score(self):
        # Finds the course the student is currently enrolled in (assuming one for simplicity)
        course = self.courses.first()
        if not course:
            return 0.0

        try:
            # Fetches the max marks configuration for this course
            max_marks_record = StudentMaxMarks.objects.get(course=course)
        except StudentMaxMarks.DoesNotExist:
            return 0.0

        # Number of times the student was marked present
        attended_count = self.attendancerecord_set.count()
        total_possible = course.total_lectures_possible
        max_attendance_marks = max_marks_record.max_attendance_marks

        if total_possible == 0 or max_attendance_marks == 0:
            return 0.0

        score = (attended_count / total_possible) * max_attendance_marks
        return round(score, 2)

# --- 3. Session Key Model (For QR Code/Location) ---


class SessionKey(models.Model):
    """Holds a unique key, expiry time, and location data for attendance scanning."""
    key = models.CharField(max_length=100, unique=True, primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    # Geolocation data required from the student
    required_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    required_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)

    # Allowed distance tolerance in meters
    location_tolerance_m = models.IntegerField(default=50)

    def __str__(self):
        return f"{self.course.course_code} - {self.key}"

# --- 4. Attendance Record Model ---


class AttendanceRecord(models.Model):
    """Logs when a student was successfully marked present for a lecture."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=50)

    # Fields to record the student's location at the time of scan
    student_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    student_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.student.full_name} present for {self.course.course_code}"

# --- 5. Student Max Marks (Configuration Model) ---


class StudentMaxMarks(models.Model):
    """Holds the maximum possible scores for the student's course."""
    # CHANGED TO OneToOneField to enforce one MaxMarks record per Course (per Django hint)
    course = models.OneToOneField(
        Course, on_delete=models.CASCADE, primary_key=True)

    # Example maximum marks
    total_class_score = models.IntegerField(default=100)
    max_attendance_marks = models.IntegerField(
        default=10)  # Max marks for attendance

    class Meta:
        verbose_name_plural = "Student Max Marks"

    def __str__(self):

        return f"Max Marks for {self.course.course_code}"
