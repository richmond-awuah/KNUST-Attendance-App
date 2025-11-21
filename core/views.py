from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from fuzzywuzzy import fuzz
from math import radians, sin, cos, sqrt, atan2
import os
import qrcode
import io
import base64
from .models import Course, Student, AttendanceRecord, SessionKey


# --- CORE VIEWS (Requires Login to Filter Data) ---

@login_required
def index(request):
    """View function for the home page of the site."""
    context = {
        'message': 'Routing is finally successful!',
        'title': 'Lecturer Dashboard',
    }
    return render(request, 'core/index.html', context=context)


@login_required
def record_attendance(request):
    """Handles the two-step attendance marking process (Select Course & Mark Students)."""

    # Filter courses to show only those taught by the logged-in user
    courses = Course.objects.filter(lecturer=request.user)
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


@login_required
def view_grades(request):
    """Handles the grade viewing process, including the warning system."""

    # Filter courses to show only those taught by the logged-in user
    courses = Course.objects.filter(lecturer=request.user)
    context = {'courses': courses, 'title': 'View Student Grades'}

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, pk=course_id)

        students_in_course = Student.objects.filter(courses=course)

        # Calculate scores and check for warnings
        student_data = []
        for student in students_in_course:
            score = student.attendance_score

            # --- WARNING LOGIC ---
            warning_status = ""

            recent_attendance = AttendanceRecord.objects.filter(
                student=student,
                course=course
            ).order_by('-timestamp')

            total_lectures = course.total_lectures_possible
            present_sessions = recent_attendance.count()
            missed_count = total_lectures - present_sessions

            # Issue warnings based on missed sessions
            if total_lectures >= 3:
                if missed_count >= 3:
                    warning_status = "CRITICAL: Missed 3 or more lectures."
                elif missed_count == 2:
                    warning_status = "WARNING: Missed 2 lectures."

            # --- END WARNING LOGIC ---

            student_data.append({
                'full_name': student.full_name,
                'index_number': student.index_number,
                'attendance_score': score,
                'warning': warning_status,
            })

        context['selected_course'] = course
        context['student_data'] = student_data

    return render(request, 'core/view_grades.html', context)


# --- ADVANCED FEATURES (QR SCAN & FUZZY MATCH) ---

def generate_qr_code(request):
    """Handles generating the QR code and starting the secure session."""

    # Filter courses to show only those taught by the logged-in user
    courses = Course.objects.filter(lecturer=request.user)

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        duration_minutes = int(request.POST.get('duration', 10))

        course = get_object_or_404(Course, pk=course_id)

        # 1. Generate a unique key
        unique_key_data = f"{course_id}|{timezone.now().timestamp()}"

        # 2. Set expiry time
        expires_at = timezone.now() + timedelta(minutes=duration_minutes)

        # 3. Save the session details to the database (Hardcoded location for now)
        session_obj = SessionKey.objects.create(
            key=unique_key_data,
            course=course,
            expires_at=expires_at,
            required_latitude=6.6710,  # Example KNUST Lat
            required_longitude=-1.5658  # Example KNUST Lon
        )

        # 4. Generate the QR code data (This will be the URL the student scans)
        # NOTE: Using a hardcoded port 8002 for local testing, replace with public URL on deployment
        public_host = f"http://127.0.0.1:8002"
        qr_content = f"{public_host}{reverse('core:scan_attendance', kwargs={'key': unique_key_data})}"

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
            'location': "6.6710 Lat, -1.5658 Lon",
            'title': 'QR Code Generated'
        }
        return render(request, 'core/qr_display.html', context)

    # GET request: Display form to select course
    context = {
        'courses': courses,
        'title': 'Generate Attendance QR'
    }
    return render(request, 'core/qr_form.html', context)


def scan_attendance(request, key):
    """Handles the student's submission via QR code scan."""

    session_obj = get_object_or_404(SessionKey, key=key)

    # 1. Check if key has expired
    if session_obj.expires_at < timezone.now():
        return render(request, 'core/scan_result.html', {'message': 'Attendance session has expired.', 'success': False})

    if request.method == 'POST':
        # Capture student data and location (if available)
        student_name_input = request.POST.get('full_name')
        index_number_input = request.POST.get('index_number')
        student_lat = request.POST.get('latitude')
        student_lon = request.POST.get('longitude')

        # 1. Find student by exact index number (Priority 1)
        try:
            student = Student.objects.get(index_number=index_number_input)
        except Student.DoesNotExist:
            student = None

        # 2. Fuzzy Name Match (Priority 2)
        if not student:
            students_in_course = Student.objects.filter(
                courses=session_obj.course)
            best_match = None
            highest_score = 0

            for s in students_in_course:
                score = fuzz.partial_ratio(
                    student_name_input.lower(), s.full_name.lower())

                if score > 85 and score > highest_score:
                    best_match = s
                    highest_score = score

            if best_match:
                student = best_match
            else:
                return render(request, 'core/scan_result.html', {'message': 'Student not found or name did not match database records.', 'success': False})

        # 3. Final verification and logging
        if student and student in session_obj.course.student_set.all():

            # --- GEOLOCATION CHECK ---
            if not student_lat or not student_lon:
                return render(request, 'core/scan_result.html', {
                    'message': 'Attendance requires geolocation. Please enable location services in your browser.',
                    'success': False
                })

            if session_obj.required_latitude and student_lat:

                # Convert degrees to radians
                lat1, lon1 = map(
                    radians, [session_obj.required_latitude, session_obj.required_longitude])
                lat2, lon2 = map(
                    radians, [float(student_lat), float(student_lon)])

                # Haversine formula to calculate distance in meters
                R = 6371  # Earth radius in km
                dlon = lon2 - lon1
                dlat = lat2 - lat1

                a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                distance_km = R * c
                distance_m = distance_km * 1000

                if distance_m > session_obj.location_tolerance_m:
                    return render(request, 'core/scan_result.html', {
                        'message': f"Attendance flagged: You are {round(distance_m)}m away, but the limit is {session_obj.location_tolerance_m}m. Please move closer to the lecture hall.",
                        'success': False
                    })
            # --- END GEOLOCATION CHECK ---

            # Mark attendance
            AttendanceRecord.objects.create(
                course=session_obj.course,
                student=student,
                session_key=session_obj.key,
                timestamp=timezone.now(),
                student_latitude=student_lat,
                student_longitude=student_lon
            )
            return render(request, 'core/scan_result.html', {'message': f'Attendance recorded for {student.full_name}!', 'success': True})

        return render(request, 'core/scan_result.html', {'message': 'Error: Student is not registered for this course.', 'success': False})

    # GET request: Display the form to the student
    context = {
        'session_key': key,
        'course_code': session_obj.course.course_code,
        'expires_at': session_obj.expires_at,
        'title': 'Record Your Attendance'
    }
    return render(request, 'core/scan_form.html', context)
