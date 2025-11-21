# core/admin.py

from django.contrib import admin
from .models import Course, Student, AttendanceRecord, StudentMaxMarks

# --- Custom Admin Class for Course ---


class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'name', 'lecturer')

    # Restrict queryset to show only courses taught by the logged-in user
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(lecturer=request.user)

    # Restrict the lecturer field dropdown to the current user
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields['lecturer'].initial = request.user
            form.base_fields['lecturer'].disabled = True
        return form


# Register models using the custom class
admin.site.register(Course, CourseAdmin)  # <-- Use the custom class
admin.site.register(Student)
admin.site.register(AttendanceRecord)
admin.site.register(StudentMaxMarks)
