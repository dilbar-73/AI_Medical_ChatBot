"""
Medical Problems Database API
This will contain predefined medical problems and their treatments
"""

MEDICAL_PROBLEMS_DATABASE = {
    "headache": {
        "symptoms": ["headache", "migraine", "head pain", "sensitivity to light"],
        "diagnosis": "Your symptoms suggest headache or migraine. Rest and hydration may help.",
        "medicines": [
            {"name": "Paracetamol 500mg", "description": "Pain reliever", "dosage": "As needed"},
            {"name": "Ibuprofen 400mg", "description": "Anti-inflammatory", "dosage": "With food"}
        ],
        "severity": "mild",
        "category": "neurological"
    },
    "chest_pain": {
        "symptoms": ["chest pain", "chest tightness", "difficulty breathing", "heart pain"],
        "diagnosis": "Chest pain requires immediate medical attention. Please visit emergency room.",
        "medicines": [
            {"name": "Aspirin 325mg", "description": "Blood thinner", "dosage": "As prescribed"},
            {"name": "Nitroglycerin", "description": "Emergency chest pain relief", "dosage": "Medical supervision only"}
        ],
        "severity": "critical",
        "category": "cardiovascular"
    },
    "fever": {
        "symptoms": ["fever", "high temperature", "body aches", "chills", "sweating"],
        "diagnosis": "Your symptoms suggest viral infection or flu. Rest and hydration are important.",
        "medicines": [
            {"name": "Paracetamol 650mg", "description": "Fever reducer", "dosage": "Every 6 hours"},
            {"name": "Vitamin C 1000mg", "description": "Immune support", "dosage": "Daily"}
        ],
        "severity": "moderate",
        "category": "infectious"
    },
    "stomach_pain": {
        "symptoms": ["stomach pain", "nausea", "vomiting", "indigestion", "bloating"],
        "diagnosis": "Stomach pain may indicate indigestion or gastritis. Avoid spicy foods.",
        "medicines": [
            {"name": "Antacid tablets", "description": "Stomach acid neutralizer", "dosage": "After meals"},
            {"name": "Omeprazole 20mg", "description": "Stomach acid reducer", "dosage": "Daily before breakfast"}
        ],
        "severity": "mild",
        "category": "gastrointestinal"
    },
    "sore_throat": {
        "symptoms": ["sore throat", "throat pain", "difficulty swallowing", "scratchy throat"],
        "diagnosis": "Sore throat may be viral or bacterial. Gargle with warm salt water.",
        "medicines": [
            {"name": "Lozenges", "description": "Throat soothing", "dosage": "As needed"},
            {"name": "Strepsils", "description": "Medicated throat relief", "dosage": "Every 2-3 hours"}
        ],
        "severity": "mild",
        "category": "respiratory"
    },
    "back_pain": {
        "symptoms": ["back pain", "lower back pain", "spine pain", "stiffness", "muscle pain"],
        "diagnosis": "Back pain often improves with gentle exercise and proper posture.",
        "medicines": [
            {"name": "Muscle relaxants", "description": "Relieve muscle tension", "dosage": "As prescribed"},
            {"name": "Topical pain gel", "description": "Localized pain relief", "dosage": "Apply to affected area"}
        ],
        "severity": "moderate",
        "category": "musculoskeletal"
    },
    "anxiety": {
        "symptoms": ["anxiety", "racing heart", "panic", "stress", "worry", "nervousness"],
        "diagnosis": "Anxiety symptoms may benefit from relaxation techniques and stress management.",
        "medicines": [
            {"name": "Lavender oil", "description": "Natural calming aid", "dosage": "Aromatherapy"},
            {"name": "Magnesium supplement", "description": "Muscle relaxation", "dosage": "Daily"}
        ],
        "severity": "moderate",
        "category": "mental_health"
    },
    "skin_rash": {
        "symptoms": ["skin rash", "itching", "allergy", "hives", "redness", "irritation"],
        "diagnosis": "Skin rashes may indicate allergic reaction. Avoid scratching and keep area clean.",
        "medicines": [
            {"name": "Hydrocortisone cream", "description": "Anti-inflammatory cream", "dosage": "Apply to rash"},
            {"name": "Antihistamine tablets", "description": "Allergy relief", "dosage": "As directed"}
        ],
        "severity": "mild",
        "category": "dermatological"
    },
    "insomnia": {
        "symptoms": ["insomnia", "sleep problems", "cannot sleep", "sleeplessness", "tired"],
        "diagnosis": "Sleep issues often improve with good sleep hygiene and stress management.",
        "medicines": [
            {"name": "Melatonin 5mg", "description": "Sleep cycle regulation", "dosage": "30 minutes before bed"},
            {"name": "Valerian root", "description": "Natural sleep aid", "dosage": "Before sleep"}
        ],
        "severity": "mild",
        "category": "sleep"
    },
    "joint_pain": {
        "symptoms": ["joint pain", "arthritis", "stiff joints", "knee pain", "joint swelling"],
        "diagnosis": "Joint pain may indicate inflammation. Gentle exercise can help.",
        "medicines": [
            {"name": "Glucosamine supplements", "description": "Joint health support", "dosage": "Daily"},
            {"name": "Omega-3 fish oil", "description": "Anti-inflammatory", "dosage": "Daily with meals"}
        ],
        "severity": "moderate",
        "category": "musculoskeletal"
    }
}

def find_medical_problem(symptoms_text):
    """
    Find medical problem from database based on symptoms
    """
    symptoms_lower = symptoms_text.lower()
    
    for problem_key, problem_data in MEDICAL_PROBLEMS_DATABASE.items():
        for symptom in problem_data["symptoms"]:
            if symptom in symptoms_lower:
                return problem_data
    
    # Default response if no match found
    return {
        "symptoms": ["unknown"],
        "diagnosis": "Your symptoms require professional medical evaluation for accurate diagnosis.",
        "medicines": [
            {"name": "General pain reliever", "description": "Over-the-counter relief", "dosage": "As needed"},
            {"name": "Multivitamins", "description": "General health support", "dosage": "Daily"}
        ],
        "severity": "unknown",
        "category": "general"
    }

def get_all_problems():
    """Get all medical problems from database"""
    return MEDICAL_PROBLEMS_DATABASE

def get_problem_by_category(category):
    """Get problems by category"""
    return {k: v for k, v in MEDICAL_PROBLEMS_DATABASE.items() if v["category"] == category}

def get_problems_by_severity(severity):
    """Get problems by severity level"""
    return {k: v for k, v in MEDICAL_PROBLEMS_DATABASE.items() if v["severity"] == severity}
