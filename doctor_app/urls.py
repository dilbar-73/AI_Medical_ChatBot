"""
AI Doctor Django Application - URL Configuration
Defines all the URL patterns for the doctor app
"""

from django.urls import path
from django.shortcuts import render
from doctor_app.views import *

# URL patterns for the AI Doctor application
urlpatterns = [
    # Main pages
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    
    # Patient workflow
    path('register/', registration, name='registration'),
    path('consultancy/', consultancy, name='consultancy'),
    path('save-consultation/', save_consultation, name='save_consultation'),
    
    # Medical features
    path('upload/', upload_image, name='upload'),
    path('location/', location_suggestions, name='location'),
    
    # Data and records
    path('database/', database_view, name='database'),
    path('patient-portal/', patient_portal, name='patient_portal'),
    
    # API endpoints
    path('api/consult-diagnose/', consultancy_diagnose, name='consultancy_diagnose'),
    path('api/check-problem/', check_patient_problem, name='check_patient_problem'),
    path('api/voice-consultation/', voice_consultation, name='voice_consultation'),
    path('api/database-diagnosis/', database_diagnosis, name='database_diagnosis'),
    
    # Utilities
    path('demo/', demo_login, name='demo_login'),
    path('voice-test/', lambda request: render(request, 'voice_test.html'), name='voice_test'),
]
