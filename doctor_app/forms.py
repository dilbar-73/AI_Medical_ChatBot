
"""
AI Doctor Django Application - Forms Module
Defines user input forms for the application
"""

from django import forms


class ImageUploadForm(forms.Form):
    """
    Form for uploading medical images for AI analysis
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your name'}),
        help_text="Enter your full name"
    )
    
    image = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        help_text="Upload a clear medical image (X-ray, scan, etc.)"
    )
    
    question = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Describe what you want to know about this image...'
            }
        ),
        help_text="Be specific about your concerns or questions"
    )
