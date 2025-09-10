from django import forms
from django.core.exceptions import ValidationError
from .models import AnalisaTebu

class AnalisaTebuForm(forms.ModelForm):
    class Meta:
        model = AnalisaTebu
        fields = ["brix", "pol", "suhu"]

    def clean_brix(self):
        brix = self.cleaned_data.get('brix')
        if brix > 100:
            brix = brix / 10
        if brix >= 100:
            raise ValidationError("Brix must be less than 100.")
        return brix

    def clean_pol(self):
        pol = self.cleaned_data.get('pol')
        if pol > 100:
            pol = pol / 10
        if pol >= 100:
            raise ValidationError("Pol must be less than 100.")
        return pol
