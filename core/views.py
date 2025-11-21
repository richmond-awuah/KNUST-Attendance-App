from .models import SessionKey
import qrcode
from django.urls import reverse  # You'll need this import too!
from datetime import timedelta, datetime
import base64
import io
from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, Student, AttendanceRecord, SessionKey
from django.utils import timezone
from fuzzywuzzy import fuzz
from datetime import timedelta
from math import radians, sin, cos, sqrt, atan2  # Added math functions here

# --- CORE VIEWS ---


def index(request):
    """View function for the home page of the site."""
    context = {
        'message': 'Routing is finally successful!',
        'title': 'Lecturer Dashboard',
    }
    return render(request, 'core/index.html', context=context)


def record_attendance(request):
    courses = Course.objects.filter(
        lecturer=request.user)  # Filter courses by user
    selected_course = None
    students = None

    if request.method == 'POST':
        # --- POST: Process Submission ---
        course_id = request.POST.get('course_id')
        session_key = request.POST.get('session_key')
        present_students_index = request.POST.getlist('present_students')

        course = get_object_or_404(Course, pk=course_id)

        # Check for duplicate session key
        if AttendanceRecord.objects.filter(session_key=session_key, course=course).exists():
            return render(request, 'core/attendance_record.html', {
                'courses': courses,
                'error_message': f'Attendance for session "{session_key}" has already been recorded for this course.',
                'title': 'Record Attendance',
            })

        # Mark attendance for all present students
        for student_index in present_students_index:
            student = get_object_or_404(Student, index_number=student_index)
            AttendanceRecord.objects.create(
                course=course,
                student=student,
                session_key=session_key,
                timestamp=timezone.now()
            )

        return redirect('core:index')

    else:
        # --- GET: Handle course selection ---
        course_id = request.GET.get('course_id')

        if course_id:
            selected_course = get_object_or_404(Course, pk=course_id)
            students = Student.objects.filter(
                courses=selected_course).order_by('full_name')

        context = {
            'courses': courses,
            'selected_course': selected_course,
            'students': students,
            'title': 'Record Attendance',
        }
        return render(request, 'core/attendance_record.html', context)


def view_grades(request):
    courses = Course.objects.filter(
        lecturer=request.user)  # Filter courses by user
    context = {'courses': courses, 'title': 'View Student Grades'}

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, pk=course_id)

        students_in_course = Student.objects.filter(courses=course)

        student_data = []
        for student in students_in_course:
            score = student.attendance_score
            student_data.append({
                'full_name': student.full_name,
                'index_number': student.index_number,
                'attendance_score': score,
            })

        context['selected_course'] = course
        context['student_data'] = student_data

    return render(request, 'core/view_grades.html', context)

# --- ADVANCED FEATURES (QR SCAN & FUZZY MATCH) ---
# core/views.py (Paste this after def view_grades(request):)


def generate_qr_code(request):
    # This view simulates the lecturer generating a QR code for a class.
    # We will hardcode the required location for now (e.g., KNUST campus center)
    REQUIRED_LAT = 6.6710
    REQUIRED_LON = -1.5658

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        duration_minutes = int(request.POST.get('duration', 10))

        course = get_object_or_404(Course, pk=course_id)

        # 1. Generate a unique key containing course ID and a timestamp
        unique_key_data = f"{course_id}|{timezone.now().timestamp()}"

        # 2. Set expiry time
        expires_at = timezone.now() + timedelta(minutes=duration_minutes)

        # 3. Save the session details to the database
        session_obj = SessionKey.objects.create(
            key=unique_key_data,
            course=course,
            expires_at=expires_at,
            required_latitude=REQUIRED_LAT,
            required_longitude=REQUIRED_LON
        )

        # 4. Generate the QR code data (This will be the URL the student scans)
        qr_content = request.build_absolute_uri(
            reverse('core:scan_attendance', kwargs={'key': unique_key_data})
        )

        # 5. Create the QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_content)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        # 6. Convert image to base64 for embedding in HTML
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_image = base64.b64encode(buffer.getvalue()).decode()

        context = {
            'qr_image': qr_image,
            'session_key': unique_key_data,
            'course': course,
            'expires_at': expires_at,
            'location': f"Lat: {REQUIRED_LAT}, Lon: {REQUIRED_LON}",
            'title': 'QR Code Generated'
        }
        return render(request, 'core/qr_display.html', context)

    # GET request: Display form to select course
    context = {
        'courses': Course.objects.all(),
        'title': 'Generate Attendance QR'
    }
    return render(request, 'core/qr_form.html', context)


def scan_attendance(request, key):
    session_obj = get_object_or_404(SessionKey, key=key)

    # Check if key has expired
    if session_obj.expires_at < timezone.now():
        return render(request, 'core/scan_result.html', {'message': 'Attendance session has expired.', 'success': False})

    if request.method == 'POST':
        # Capture student data and location (if available)
        student_name_input = request.POST.get('full_name')
        index_number_input = request.POST.get('index_number')
        student_lat = request.POST.get('latitude')
        student_lon = request.POST.get('longitude')

        # 1.
