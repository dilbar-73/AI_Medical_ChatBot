"""
AI Doctor Django Application - Main Views
This file handles all the main functionality for our medical consultation system.
It's written to be easy to read and understand, like a real developer would write it.
"""

# Django imports we need
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from datetime import datetime, timedelta
import json
import random
import string
import base64
import io
import wave
import numpy as np
from django.conf import settings
from django.views.decorators.http import require_http_methods

# Our custom modules
from .forms import ImageUploadForm
from .brain_of_the_doctor import analyze_medical_image
from .models import UserProfile, Consultation, PatientInfo
from .medical_database import find_medical_problem, get_all_problems, get_problem_by_category, get_problems_by_severity


def is_admin(user):
    """Check if the user is an admin/superuser"""
    return user.is_authenticated and user.is_superuser


def generate_referral_number():
    """Generate a unique 8-character referral number for patients"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def registration(request):
    """
    Handle new patient registration
    Creates a unique referral number and saves patient info
    """
    if request.method == 'POST':
        # First, generate a unique referral number
        referral_number = generate_referral_number()
        
        # Keep generating until we find one that doesn't exist
        while PatientInfo.objects.filter(referral_number=referral_number).exists():
            referral_number = generate_referral_number()
        
        # Now create the patient record with all their info
        patient = PatientInfo.objects.create(
            referral_number=referral_number,
            name=request.POST.get('name', ''),
            email=request.POST.get('contact_email', ''),
            phone=request.POST.get('contact_phone', ''),
            age=request.POST.get('age', 0) if request.POST.get('age') else None,
            gender=request.POST.get('gender', '') if request.POST.get('gender') != 'Select' else '',
            specialization='general',  # Default to general practice
            medical_history=request.POST.get('medical_history', '')
        )
        
        # Save the referral number in session so we can use it later
        request.session['referral_number'] = referral_number
        request.session['patient_name'] = patient.name
        
        # Send them straight to the consultation page
        return redirect('consultancy')
    
    # If it's a GET request, just show the registration form
    return render(request, 'registration.html')

def home(request):
    """Simple home page - redirects to clinic home"""
    return render(request, 'clinic/home.html')


def dashboard(request):
    """
    Admin dashboard with statistics and recent activity
    Shows patient counts, consultation stats, and recent cases
    """
    # Get today's date for our statistics
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # Calculate some useful stats for the dashboard
    stats = {
        'total_patients': PatientInfo.objects.count(),
        'total_consultations': Consultation.objects.count(),
        'consultations_today': Consultation.objects.filter(created_at__date=today).count(),
        'consultations_week': Consultation.objects.filter(created_at__date__gte=week_ago).count(),
    }
    
    # Get the 10 most recent consultations to show on dashboard
    recent_consultations = Consultation.objects.select_related('patient').order_by('-created_at')[:10]
    
    return render(request, 'dashboard.html', {
        'stats': stats,
        'recent_consultations': recent_consultations
    })

def consultancy(request):
    """
    Main consultation page - where patients describe their symptoms
    Requires a valid referral number to access
    """
    referral_number = request.session.get('referral_number')
    if not referral_number:
        # No referral number? Send them back to register first
        return render(request, 'no_referral.html', {
            'message': 'Please register first to get a referral number',
            'action_url': 'registration'
        })
    
    try:
        # Look up the patient using their referral number
        patient = PatientInfo.objects.get(referral_number=referral_number)
        return render(request, 'consultancy.html', {
            'referral_number': referral_number,
            'patient': patient
        })
    except PatientInfo.DoesNotExist:
        # Referral number not found in our database
        return render(request, 'no_referral.html', {
            'message': 'Invalid referral number. Please register again.',
            'action_url': 'registration'
        })

'Save consultation data from the consultation page - expects JSON data with diagnosis, medicines, and symptoms'
@csrf_exempt
def save_consultation(request):
    """
    Save consultation data from the frontend
    Called via AJAX when a patient completes a consultation
    """
    if request.method == 'POST':
        try:
            # Get the referral number from the session
            referral_number = request.session.get('referral_number')
            if not referral_number:
                return JsonResponse({'success': False, 'error': 'No referral number found'})
            
            # Find the patient using their referral number
            patient = PatientInfo.objects.get(referral_number=referral_number)
            
            # Parse the JSON data from the frontend
            data = json.loads(request.body)
            
            # Create a new consultation record
            consultation = Consultation.objects.create(
                patient=patient,
                diagnosis=data.get('diagnosis', ''),
                medicines=data.get('medicines', []),
                symptoms=data.get('symptoms', '')
            )
            
            # Return success with the consultation ID
            return JsonResponse({'success': True, 'consultation_id': consultation.id})
            
        except Exception as e:
            # Something went wrong - return error message
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Only POST requests are allowed
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@user_passes_test(is_admin, login_url='/admin/', redirect_field_name=None)
def database_view(request):
    'Admin-only can access database view - shows patient consultations'
    referral_number = request.session.get('referral_number')
    if not referral_number:
        return render(request, 'no_referral.html', {
            'message': 'Please register first to get a referral number',
            'action_url': 'registration'
        })
    
    try:
        # Get patient and their consultation history
        patient = PatientInfo.objects.get(referral_number=referral_number)
        consultations = Consultation.objects.filter(patient=patient).order_by('-created_at')
        
        return render(request, 'database.html', {
            'patient': patient,
            'consultations': consultations
        })
    except PatientInfo.DoesNotExist:
        return render(request, 'no_referral.html', {
            'message': 'Invalid referral number. Please register again.',
            'action_url': 'registration'
        })

'Handle patient portal access - allows patients to view their consultation history using their phone number'
def patient_portal(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        if phone_number:
            try:
                # Find patient by phone number
                patient = PatientInfo.objects.get(phone=phone_number)
                consultations = Consultation.objects.filter(patient=patient).order_by('-created_at')
                
                return render(request, 'patient_portal.html', {
                    'patient': patient,
                    'consultations': consultations,
                    'phone_number': phone_number
                })
            except PatientInfo.DoesNotExist:
                # No patient found with this number
                return render(request, 'patient_portal.html', {
                    'error': 'No patient found with this phone number',
                    'phone_number': phone_number
                })
        else:
            # Empty phone number
            return render(request, 'patient_portal.html', {
                'error': 'Please enter a phone number'
            })
    
    # Just show the search form
    return render(request, 'patient_portal.html')


'Demo login for testing - sets a demo referral number in the session and redirects to consultation page'
def demo_login(request):
    request.session['referral_number'] = 'DEMO1234'
    return redirect('consultancy')

'Show nearby medical locations'
def location_suggestions(request):
    referral_number = request.session.get('referral_number')
    if not referral_number:
        return render(request, 'no_referral.html', {
            'message': 'Please register first to get a referral number',
            'action_url': 'registration'
        })
    
    return render(request, 'location.html', {
        'referral_number': referral_number
    })
    
'Handle medical image upload and analysis - sends the image and question to the AI module and shows results'
@csrf_exempt
@require_http_methods(["POST"])
def check_patient_problem(request):
    """
    API endpoint to check patient's problem/diagnosis
    Works the same way as current consultation system
    
    Expected JSON payload:
    {
        "api_key": "your_api_key",
        "symptoms": "patient symptoms",
        "patient_info": {
            "name": "patient name",
            "age": "age",
            "gender": "gender"
        }
    }
    """
    try:
        # Get API key from request
        data = json.loads(request.body)
        provided_api_key = data.get('api_key', '')
        
        # Check if API key is valid (you can set this in settings.py)
        valid_api_key = getattr(settings, 'AI_DOCTOR_API_KEY', 'DEFAULT_API_KEY_12345')
        
        if provided_api_key != valid_api_key:
            return JsonResponse({
                'success': False,
                'error': 'Invalid API key',
                'status_code': 401
            }, status=401)
        
        # Extract patient information
        symptoms = data.get('symptoms', '').lower()
        patient_info = data.get('patient_info', {})
        
        # Different diagnosis based on specific symptoms
        diagnosis = ""
        suggested_medicines = []
        
        if 'headache' in symptoms or 'migraine' in symptoms:
            if 'sensitivity to light' in symptoms:
                diagnosis = "Your symptoms suggest migraine with photophobia. I recommend rest in a dark room and consult a neurologist."
                suggested_medicines = [
                    {"name": "Sumatriptan 100mg", "description": "Migraine relief medication", "dosage": "Take at onset of migraine"},
                    {"name": "Paracetamol 500mg", "description": "Pain reliever for mild symptoms", "dosage": "As needed for pain"}
                ]
            else:
                diagnosis = "Your symptoms suggest tension headache. Stress management and regular sleep may help."
                suggested_medicines = [
                    {"name": "Ibuprofen 400mg", "description": "Anti-inflammatory for headache", "dosage": "Take with food"},
                    {"name": "Caffeine tablets", "description": "Headache relief", "dosage": "As needed"}
                ]
        
        elif 'chest pain' in symptoms or 'difficulty breathing' in symptoms:
            diagnosis = "Chest pain with breathing difficulty requires immediate medical attention. Please visit emergency room."
            suggested_medicines = [
                {"name": "Aspirin 325mg", "description": "Blood thinner for heart health", "dosage": "As prescribed by cardiologist"},
                {"name": "Nitroglycerin", "description": "Emergency chest pain relief", "dosage": "Only under medical supervision"}
            ]
        
        elif 'fever' in symptoms and ('cough' in symptoms or 'body aches' in symptoms):
            diagnosis = "Your symptoms suggest viral infection or flu. Rest, hydration, and monitoring temperature are important."
            suggested_medicines = [
                {"name": "Paracetamol 650mg", "description": "Fever reducer and pain relief", "dosage": "Every 6 hours as needed"},
                {"name": "Dextromethorphan", "description": "Cough suppressant", "dosage": "As directed on packaging"},
                {"name": "Vitamin C 1000mg", "description": "Immune system support", "dosage": "Daily during illness"}
            ]
        
        elif 'stomach pain' in symptoms or 'nausea' in symptoms:
            if 'after eating' in symptoms:
                diagnosis = "Your symptoms suggest indigestion or gastritis. Avoid spicy foods and eat smaller meals."
                suggested_medicines = [
                    {"name": "Antacid tablets", "description": "Stomach acid neutralizer", "dosage": "After meals as needed"},
                    {"name": "Omeprazole 20mg", "description": "Stomach acid reducer", "dosage": "Once daily before breakfast"},
                    {"name": "Pepto-Bismol", "description": "Stomach upset relief", "dosage": "As directed"}
                ]
            else:
                diagnosis = "Stomach pain and nausea may indicate gastroenteritis. Stay hydrated and consider BRAT diet."
                suggested_medicines = [
                    {"name": "Oral rehydration salts", "description": "Fluid and electrolyte replacement", "dosage": "Mix with water as directed"},
                    {"name": "Loperamide", "description": "Anti-diarrheal medication", "dosage": "As needed"}
                ]
        
        elif 'sore throat' in symptoms:
            diagnosis = "Sore throat may be viral or bacterial. Gargle with warm salt water and avoid irritants."
            suggested_medicines = [
                {"name": "Lozenges", "description": "Throat soothing", "dosage": "As needed"},
                {"name": "Strepsils", "description": "Medicated throat relief", "dosage": "Every 2-3 hours"},
                {"name": "Amoxicillin", "description": "Antibiotic for bacterial infections", "dosage": "As prescribed by doctor"}
            ]
        
        elif 'back pain' in symptoms:
            diagnosis = "Back pain often improves with gentle exercise and proper posture. Consider physical therapy."
            suggested_medicines = [
                {"name": "Muscle relaxants", "description": "Relieve muscle tension", "dosage": "As prescribed"},
                {"name": "Topical pain relief gel", "description": "Localized pain relief", "dosage": "Apply to affected area"},
                {"name": "NSAID pain relievers", "description": "Anti-inflammatory pain relief", "dosage": "With food as needed"}
            ]
        
        elif 'eye strain' in symptoms or 'blurred vision' in symptoms or 'vision' in symptoms:
            diagnosis = "Eye strain from digital screens is common. Follow the 20-20-20 rule and consider computer glasses."
            suggested_medicines = [
                {"name": "Lubricating eye drops", "description": "Relieve dry eyes", "dosage": "As needed"},
                {"name": "Vitamin A supplement", "description": "Eye health support", "dosage": "Daily"},
                {"name": "Blue light blocking glasses", "description": "Reduce eye strain", "dosage": "Wear during screen time"}
            ]
        
        elif 'anxiety' in symptoms or 'racing heart' in symptoms or 'panic' in symptoms:
            diagnosis = "Anxiety symptoms may benefit from relaxation techniques and stress management. Consider counseling."
            suggested_medicines = [
                {"name": "Lavender essential oil", "description": "Natural calming aid", "dosage": "Use as aromatherapy"},
                {"name": "Magnesium supplement", "description": "Muscle relaxation and calm", "dosage": "Daily as directed"},
                {"name": "Chamomile tea", "description": "Natural relaxation", "dosage": "Before bedtime"}
            ]
        
        elif 'skin rash' in symptoms or 'itching' in symptoms or 'allergy' in symptoms:
            diagnosis = "Skin rashes may indicate allergic reaction or skin condition. Avoid scratching and keep area clean."
            suggested_medicines = [
                {"name": "Hydrocortisone cream", "description": "Anti-inflammatory skin cream", "dosage": "Apply to affected area"},
                {"name": "Antihistamine tablets", "description": "Allergy relief", "dosage": "As directed"},
                {"name": "Calamine lotion", "description": "Soothes itching and irritation", "dosage": "Apply to rash"}
            ]
        
        elif 'insomnia' in symptoms or 'sleep' in symptoms or 'cannot sleep' in symptoms:
            diagnosis = "Sleep issues often improve with good sleep hygiene and stress management. Avoid screens before bed."
            suggested_medicines = [
                {"name": "Melatonin 5mg", "description": "Sleep cycle regulation", "dosage": "30 minutes before bedtime"},
                {"name": "Valerian root", "description": "Natural sleep aid", "dosage": "Before sleep"},
                {"name": "Lavender pillow spray", "description": "Relaxing aroma", "dosage": "Spray on pillow before bed"}
            ]
        
        elif 'dizziness' in symptoms or 'vertigo' in symptoms:
            diagnosis = "Dizziness may indicate inner ear issues or dehydration. Sit down immediately and stay hydrated."
            suggested_medicines = [
                {"name": "Meclizine", "description": "Motion sickness relief", "dosage": "As needed for dizziness"},
                {"name": "Electrolyte drinks", "description": "Hydration support", "dosage": "Throughout the day"},
                {"name": "Ginger supplements", "description": "Natural nausea relief", "dosage": "As needed"}
            ]
        
        elif 'joint pain' in symptoms or 'arthritis' in symptoms:
            diagnosis = "Joint pain may indicate inflammation. Gentle exercise and weight management can help."
            suggested_medicines = [
                {"name": "Glucosamine supplements", "description": "Joint health support", "dosage": "Daily"},
                {"name": "Omega-3 fish oil", "description": "Anti-inflammatory", "dosage": "Daily with meals"},
                {"name": "Topical joint cream", "description": "Localized pain relief", "dosage": "Apply to joints"}
            ]
        
        else:
            # Default response for unclear symptoms
            diagnosis = "Your symptoms require professional medical evaluation for accurate diagnosis."
            suggested_medicines = [
                {"name": "General pain reliever", "description": "Over-the-counter pain relief", "dosage": "As needed"},
                {"name": "Multivitamins", "description": "General health support", "dosage": "Daily"}
            ]
        
        # Return response in same format as current system
        return JsonResponse({
            'success': True,
            'diagnosis': diagnosis,
            'medicines': suggested_medicines,
            'symptoms_analyzed': symptoms,
            'patient': patient_info,
            'timestamp': datetime.now().isoformat(),
            'consultation_id': f"API_{random.randint(1000, 9999)}"
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data',
            'status_code': 400
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}',
            'status_code': 500
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def voice_consultation(request):
    """
    Voice API endpoint - accepts voice notes and returns voice response
    Works with base64 encoded audio data
    
    Expected JSON payload:
    {
        "api_key": "your_api_key",
        "voice_note": "base64_encoded_audio_data",
        "patient_info": {
            "name": "patient name",
            "age": "age",
            "gender": "gender"
        },
        "format": "webm|wav|mp3" (optional, defaults to wav)
    }
    """
    try:
        # Get API key from request
        data = json.loads(request.body)
        provided_api_key = data.get('api_key', '')
        
        # Check if API key is valid
        valid_api_key = getattr(settings, 'AI_DOCTOR_API_KEY', 'DEFAULT_API_KEY_12345')
        
        if provided_api_key != valid_api_key:
            return JsonResponse({
                'success': False,
                'error': 'Invalid API key',
                'status_code': 401
            }, status=401)
        
        # Extract voice data
        voice_note_base64 = data.get('voice_note', '')
        patient_info = data.get('patient_info', {})
        audio_format = data.get('format', 'wav')
        
        if not voice_note_base64:
            return JsonResponse({
                'success': False,
                'error': 'No voice note provided',
                'status_code': 400
            }, status=400)
        
        # Decode base64 audio data
        try:
            audio_data = base64.b64decode(voice_note_base64)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid audio data: {str(e)}',
                'status_code': 400
            }, status=400)
        
        # Simulate voice-to-text conversion (in production, use speech recognition API)
        # For now, we'll simulate different symptoms based on the audio size
        simulated_symptoms = simulate_voice_to_text(audio_data)
        
        # Use the same diagnosis logic as check_patient_problem
        symptoms = simulated_symptoms.lower()
        diagnosis = ""
        suggested_medicines = []
        
        # Same diagnosis logic as before
        if 'headache' in symptoms or 'migraine' in symptoms:
            if 'sensitivity to light' in symptoms:
                diagnosis = "Your symptoms suggest migraine with photophobia. I recommend rest in a dark room and consult a neurologist."
                suggested_medicines = [
                    {"name": "Sumatriptan 100mg", "description": "Migraine relief medication", "dosage": "Take at onset of migraine"},
                    {"name": "Paracetamol 500mg", "description": "Pain reliever for mild symptoms", "dosage": "As needed for pain"}
                ]
            else:
                diagnosis = "Your symptoms suggest tension headache. Stress management and regular sleep may help."
                suggested_medicines = [
                    {"name": "Ibuprofen 400mg", "description": "Anti-inflammatory for headache", "dosage": "Take with food"},
                    {"name": "Caffeine tablets", "description": "Headache relief", "dosage": "As needed"}
                ]
        
        elif 'chest pain' in symptoms or 'difficulty breathing' in symptoms:
            diagnosis = "Chest pain with breathing difficulty requires immediate medical attention. Please visit emergency room."
            suggested_medicines = [
                {"name": "Aspirin 325mg", "description": "Blood thinner for heart health", "dosage": "As prescribed by cardiologist"},
                {"name": "Nitroglycerin", "description": "Emergency chest pain relief", "dosage": "Only under medical supervision"}
            ]
        
        elif 'fever' in symptoms and ('cough' in symptoms or 'body aches' in symptoms):
            diagnosis = "Your symptoms suggest viral infection or flu. Rest, hydration, and monitoring temperature are important."
            suggested_medicines = [
                {"name": "Paracetamol 650mg", "description": "Fever reducer and pain relief", "dosage": "Every 6 hours as needed"},
                {"name": "Dextromethorphan", "description": "Cough suppressant", "dosage": "As directed on packaging"},
                {"name": "Vitamin C 1000mg", "description": "Immune system support", "dosage": "Daily during illness"}
            ]
        
        else:
            # Default response for unclear symptoms
            diagnosis = "Your symptoms require professional medical evaluation for accurate diagnosis."
            suggested_medicines = [
                {"name": "General pain reliever", "description": "Over-the-counter pain relief", "dosage": "As needed"},
                {"name": "Multivitamins", "description": "General health support", "dosage": "Daily"}
            ]
        
        # Generate voice response (text-to-speech simulation)
        voice_response_base64 = generate_voice_response(diagnosis, suggested_medicines)
        
        # Return response with voice data
        return JsonResponse({
            'success': True,
            'symptoms_detected': simulated_symptoms,
            'diagnosis': diagnosis,
            'medicines': suggested_medicines,
            'voice_response': voice_response_base64,
            'voice_format': 'wav',
            'patient': patient_info,
            'timestamp': datetime.now().isoformat(),
            'consultation_id': f"VOICE_{random.randint(1000, 9999)}"
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data',
            'status_code': 400
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}',
            'status_code': 500
        }, status=500)


def simulate_voice_to_text(audio_data):
    """
    Simulate voice-to-text conversion
    In production, integrate with Google Speech-to-Text, Azure Speech, etc.
    """
    # For demo purposes, simulate different symptoms based on audio data size
    audio_size = len(audio_data)
    
    if audio_size < 1000:
        return "I have headache and sensitivity to light"
    elif audio_size < 2000:
        return "I have chest pain and difficulty breathing"
    elif audio_size < 3000:
        return "I have high fever, dry cough, and body aches"
    elif audio_size < 4000:
        return "I have stomach pain and nausea after eating"
    else:
        return "I have sore throat and difficulty swallowing"


def generate_voice_response(diagnosis, medicines):
    """
    Generate voice response (text-to-speech simulation)
    In production, integrate with Google Text-to-Speech, Azure Speech, etc.
    """
    # Create response text
    response_text = f"Diagnosis: {diagnosis}. "
    response_text += "Recommended medicines: "
    for medicine in medicines:
        response_text += f"{medicine['name']}, "
    response_text += "Please consult a healthcare professional for proper medical advice."
    
    # For demo purposes, return a simple base64 encoded WAV file
    # In production, use actual TTS service
    return create_simple_wav_base64(response_text)


def create_simple_wav_base64(text):
    """
    Create a simple WAV file with text (demo only)
    In production, use actual text-to-speech service
    """
    # Create a simple WAV file (demo - just returns base64 of the text)
    # In production, this would generate actual audio
    text_bytes = text.encode('utf-8')
    
    # Create a simple WAV header and data
    sample_rate = 44100
    duration = 2.0  # 2 seconds
    frequency = 440  # A4 note
    
    # Generate simple sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(frequency * t * 2 * np.pi)
    
    # Convert to 16-bit integers
    tone = (tone * 32767).astype(np.int16)
    
    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(tone.tobytes())
    
    # Encode to base64
    wav_buffer.seek(0)
    wav_base64 = base64.b64encode(wav_buffer.read()).decode('utf-8')
    
    return wav_base64


@csrf_exempt
@require_http_methods(["POST", "GET"])
def database_diagnosis(request):
    """
    Database-driven API endpoint - directly fetches problems from database
    More accurate and consistent diagnosis using predefined medical database
    
    POST: Analyze symptoms against database
    GET: Get database information
    
    POST Expected JSON payload:
    {
        "api_key": "your_api_key",
        "symptoms": "patient symptoms text",
        "patient_info": {
            "name": "patient name",
            "age": "age",
            "gender": "gender"
        }
    }
    
    GET Query parameters:
    ?action=all - Get all problems
    ?action=category&category=neurological - Get problems by category
    ?action=severity&severity=critical - Get problems by severity
    """
    try:
        # Check API key
        if request.method == "POST":
            data = json.loads(request.body)
            provided_api_key = data.get('api_key', '')
        else:
            provided_api_key = request.GET.get('api_key', '')
        
        valid_api_key = getattr(settings, 'AI_DOCTOR_API_KEY', 'DEFAULT_API_KEY_12345')
        
        if provided_api_key != valid_api_key:
            return JsonResponse({
                'success': False,
                'error': 'Invalid API key',
                'status_code': 401
            }, status=401)
        
        if request.method == "POST":
            # Analyze symptoms against database
            symptoms = data.get('symptoms', '')
            patient_info = data.get('patient_info', {})
            
            # Find problem in database
            problem_result = find_medical_problem(symptoms)
            
            return JsonResponse({
                'success': True,
                'symptoms_analyzed': symptoms,
                'diagnosis': problem_result['diagnosis'],
                'medicines': problem_result['medicines'],
                'severity': problem_result['severity'],
                'category': problem_result['category'],
                'patient': patient_info,
                'timestamp': datetime.now().isoformat(),
                'consultation_id': f"DB_{random.randint(1000, 9999)}",
                'source': 'database'
            })
        
        else:  # GET request
            action = request.GET.get('action', '')
            
            if action == 'all':
                # Get all problems from database
                all_problems = get_all_problems()
                return JsonResponse({
                    'success': True,
                    'action': 'all_problems',
                    'total_problems': len(all_problems),
                    'problems': all_problems
                })
            
            elif action == 'category':
                category = request.GET.get('category', '')
                if category:
                    category_problems = get_problem_by_category(category)
                    return JsonResponse({
                        'success': True,
                        'action': 'category_problems',
                        'category': category,
                        'total_problems': len(category_problems),
                        'problems': category_problems
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Category parameter required',
                        'status_code': 400
                    }, status=400)
            
            elif action == 'severity':
                severity = request.GET.get('severity', '')
                if severity:
                    severity_problems = get_problems_by_severity(severity)
                    return JsonResponse({
                        'success': True,
                        'action': 'severity_problems',
                        'severity': severity,
                        'total_problems': len(severity_problems),
                        'problems': severity_problems
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Severity parameter required',
                        'status_code': 400
                    }, status=400)
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action. Use: all, category, or severity',
                    'status_code': 400
                }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data',
            'status_code': 400
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}',
            'status_code': 500
        }, status=500)


def upload_image(request):
    referral_number = request.session.get('referral_number')
    if not referral_number:
        # Need to register first
        return redirect('registration')

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid():
            # Get the form data
            name = form.cleaned_data["name"]
            image = request.FILES["image"]
            question = form.cleaned_data["question"]

            # Send to AI for analysis
            result = analyze_medical_image(image, question)

            # Show the results
            return render(request,"result.html", {
                "name": name,
                "result": result
            })

    else:
        # Just show the upload form
        form = ImageUploadForm()

    return render(request,"upload.html",{"form":form})
