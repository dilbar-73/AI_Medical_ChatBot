"""
AI Doctor Django Application - URL Configuration
Defines all the URL patterns for the doctor app
"""

from django.urls import path
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
    
    # Utilities
    path('demo/', views.demo_login, name='demo_login'),
]
