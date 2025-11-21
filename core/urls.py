# core/urls.py
from . import views
from django.urls import path
app_name = 'core'


urlpatterns = [
    path('', views.index, name='index'),
    path('attendance/record/', views.record_attendance, name='record_attendance'),
    path('grades/', views.view_grades, name='view_grades'),

    path('attendance/generate/', views.generate_qr_code, name='generate_qr_code'),
    path('attendance/scan/<str:key>/',
         views.scan_attendance, name='scan_attendance'),
]
