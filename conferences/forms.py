from django import forms
from .models import Conference

class ConferenceForm(forms.ModelForm):
    class Meta:
        model = Conference
        fields = ['name', 'key', 'domain', 'date', 'location', 'audience', 'acts']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }