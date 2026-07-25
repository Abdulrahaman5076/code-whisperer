"""
Code Whisperer - Forms
Form validation and processing for code submission.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings

class CodeAnalysisForm(forms.Form):
    """Form for submitting code for analysis."""
    
    code = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'code-input',
            'placeholder': '# Paste your AI-generated Python code here...\n\ndef main():\n    print("Hello, World!")\n',
            'rows': 15,
            'spellcheck': 'false',
        }),
        label='Your Code',
        help_text='Supports Python, JavaScript, and TypeScript.'
    )
    
    api_key = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'api-key-input',
            'placeholder': 'Enter your Gemini API key (optional)',
        }),
        label='Gemini API Key',
        help_text='Get a free key at aistudio.google.com'
    )
    
    language = forms.ChoiceField(
        choices=[
            ('auto', 'Auto Detect'),
            ('python', 'Python'),
            ('javascript', 'JavaScript'),
            ('typescript', 'TypeScript'),
        ],
        initial='auto',
        required=False,
        widget=forms.Select(attrs={'class': 'language-select'}),
    )
    
    def clean_code(self):
        """Validate the submitted code."""
        code = self.cleaned_data.get('code', '')
        
        if not code or not code.strip():
            raise ValidationError("Please paste some code to analyze.")
        
        if len(code) > settings.MAX_CODE_LENGTH:
            raise ValidationError(
                f"Code is too long. Maximum {settings.MAX_CODE_LENGTH:,} characters. "
                f"Yours has {len(code):,}."
            )
        
        if len(code.splitlines()) > settings.MAX_CODE_LINES:
            raise ValidationError(
                f"Too many lines. Maximum {settings.MAX_CODE_LINES:,} lines."
            )
        
        # Check for dangerous patterns
        blocked_patterns = [
            'os.system(', 'subprocess.call(', 'eval(', 'exec(',
            '__import__(', 'rm -rf', 'DROP TABLE',
        ]
        for pattern in blocked_patterns:
            if pattern in code:
                raise ValidationError(
                    f"Potentially dangerous code detected: '{pattern}'. "
                    "This is blocked for security reasons."
                )
        
        return code
    
    def clean_api_key(self):
        """Validate the API key if provided."""
        api_key = self.cleaned_data.get('api_key', '')
        if api_key and len(api_key) < 10:
            raise ValidationError("API key seems too short. Please check and try again.")
        return api_key