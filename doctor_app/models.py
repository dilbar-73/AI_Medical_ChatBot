"""
AI Doctor Django Application - Database Models
Defines the database structure for patients, consultations, and user profiles
"""

from django.db import models
from django.contrib.auth.models import User

'Patient model to store basic patient information and medical image analysis'
class Patient(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='patients/')
    question = models.TextField()
    diagnosis = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name


'Extended user profile to store additional information about doctors and patients'
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=254, default='')
    phone = models.CharField(max_length=15, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True)
    specialization = models.CharField(max_length=20, blank=True, choices=[
        ('general', 'General Practice'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('pediatrics', 'Pediatrics'),
        ('orthopedics', 'Orthopedics')
    ])

    def __str__(self):
        return self.user.username

'Patient information and medical history'
class PatientInfo(models.Model):
    referral_number = models.CharField(max_length=10, unique=True, help_text="Unique patient referral number")
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True)
    specialization = models.CharField(max_length=20, choices=[
        ('general', 'General Practice'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('pediatrics', 'Pediatrics'),
        ('orthopedics', 'Orthopedics')
    ], default='general')
    medical_history = models.TextField(blank=True, help_text="Patient's medical history and notes")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.referral_number}"


'Medical consultation records'
class Consultation(models.Model):
    patient = models.ForeignKey(PatientInfo, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    diagnosis = models.TextField(help_text="AI or doctor diagnosis")
    medicines = models.JSONField(default=list, help_text="List of prescribed medicines")
    symptoms = models.TextField(blank=True, help_text="Patient reported symptoms")
    voice_note = models.FileField(upload_to='voice_notes/', blank=True)
    medical_image = models.ImageField(upload_to='medical_images/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Smart string representation based on what's available
        if self.patient:
            return f"Consultation by {self.patient.name} on {self.created_at.strftime('%Y-%m-%d')}"
        elif self.user:
            return f"Consultation by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"
        return f"Consultation on {self.created_at.strftime('%Y-%m-%d')}"
