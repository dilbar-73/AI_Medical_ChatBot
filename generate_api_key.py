"""
API Key Generator for AI Doctor Application
Generate secure API keys for your application
"""

import secrets
import string

def generate_api_key():
    """Generate a secure random API key"""
    # Generate 32 character random string
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    # Add prefix for identification
    return f"AI_DOC_{api_key}"

def main():
    print("=== AI Doctor API Key Generator ===")
    print("\nGenerated API Key:")
    print(generate_api_key())
    print("\nCopy this key to your settings.py file:")
    print("AI_DOCTOR_API_KEY = 'YOUR_GENERATED_KEY_HERE'")
    print("\n" + "="*40)

if __name__ == "__main__":
    main()
