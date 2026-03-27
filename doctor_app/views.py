'''This Is the main views file for the  Django application. It handles all the core logic for patient registration, consultation, and admin database access.
The code is structured to be simple and easy to understand, with clear comments.
The AI analysis is currently a placeholder, but the structure allows for easy integration of real AI/ML models in the future.'''

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from datetime import datetime, timedelta
import json
import random
import string

# Import our custom modules
from .forms import ImageUploadForm
from .brain_of_the_doctor import analyze_medical_image
from .models import UserProfile, Consultation, PatientInfo


'Function to check if user is admin'
def is_admin(user):
    return user.is_authenticated and user.is_superuser

'Generate unique 8-character referral number for patients'
def generate_referral_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

'Handle patient registration'
def registration(request):
    if request.method == 'POST':
        # Generate unique referral number
        referral_number = generate_referral_number()
        
        # Make sure it's actually unique
        while PatientInfo.objects.filter(referral_number=referral_number).exists():
            referral_number = generate_referral_number()
        
        # Create new patient record
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
        
        # Save patient info in session for later use
        request.session['referral_number'] = referral_number
        request.session['patient_name'] = patient.name
        
        # Send them straight to consultation
        return redirect('consultancy')
    
    # Just show the registration form
    return render(request, 'registration.html')

'Home page view - simple redirects to clinic home'
def home(request):
    return render(request, 'clinic/home.html')


'Dashboard view - shows stats and recent consultations for admin users'
def dashboard(request):
    # Get today's date for statistics
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # Calculate some useful stats
    stats = {
        'total_patients': PatientInfo.objects.count(),
        'total_consultations': Consultation.objects.count(),
        'consultations_today': Consultation.objects.filter(created_at__date=today).count(),
        'consultations_week': Consultation.objects.filter(created_at__date__gte=week_ago).count(),
    }
    
    # Get the 10 most recent consultations
    recent_consultations = Consultation.objects.select_related('patient').order_by('-created_at')[:10]
    
    return render(request, 'dashboard.html', {
        'stats': stats,
        'recent_consultations': recent_consultations
    })

def consultancy(request):
    """Main consultation page - requires valid referral number"""
    referral_number = request.session.get('referral_number')
    if not referral_number:
        # No referral number? Send them back to register
        return render(request, 'no_referral.html', {
            'message': 'Please register first to get a referral number',
            'action_url': 'registration'
        })
    
    try:
        # Find the patient with this referral number
        patient = PatientInfo.objects.get(referral_number=referral_number)
        return render(request, 'consultancy.html', {
            'referral_number': referral_number,
            'patient': patient
        })
    except PatientInfo.DoesNotExist:
        # Referral number not found in database
        return render(request, 'no_referral.html', {
            'message': 'Invalid referral number. Please register again.',
            'action_url': 'registration'
        })

'Save consultation data from the consultation page - expects JSON data with diagnosis, medicines, and symptoms'
@csrf_exempt
def save_consultation(request):
    if request.method == 'POST':
        try:
            referral_number = request.session.get('referral_number')
            if not referral_number:
                return JsonResponse({'success': False, 'error': 'No referral number found'})
            
            # Get the patient record
            patient = PatientInfo.objects.get(referral_number=referral_number)
            data = json.loads(request.body)
            
            # Create new consultation record
            consultation = Consultation.objects.create(
                patient=patient,
                diagnosis=data.get('diagnosis', ''),
                medicines=data.get('medicines', []),
                symptoms=data.get('symptoms', '')
            )
            
            return JsonResponse({'success': True, 'consultation_id': consultation.id})
        except Exception as e:
            # Something went wrong - log it and return error
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Only POST requests allowed
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
