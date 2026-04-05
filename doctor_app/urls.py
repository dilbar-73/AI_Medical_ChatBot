"""
AI Doctor Django Application - URL Configuration
Defines all the URL patterns for the doctor app
"""

from django.urls import path
from django.shortcuts import render
from . import views

# URL patterns for the AI Doctor application
urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Patient workflow
    path('register/', views.registration, name='registration'),
    path('consultancy/', views.consultancy, name='consultancy'),
    path('save-consultation/', views.save_consultation, name='save_consultation'),
    
    # Medical features
    path('upload/', views.upload_image, name='upload'),
    path('location/', views.location_suggestions, name='location'),
    
    # Data and records
    path('database/', views.database_view, name='database'),
    path('patient-portal/', views.patient_portal, name='patient_portal'),
    
    # API endpoints
    path('api/consult-diagnose/', views.consultancy_diagnose, name='consultancy_diagnose'),
    path('api/check-problem/', views.check_patient_problem, name='check_patient_problem'),
    path('api/voice-consultation/', views.voice_consultation, name='voice_consultation'),
    path('api/database-diagnosis/', views.database_diagnosis, name='database_diagnosis'),
    
    # Utilities
    path('demo/', views.demo_login, name='demo_login'),
    path('voice-test/', lambda request: render(request, 'voice_test.html'), name='voice_test'),
]
