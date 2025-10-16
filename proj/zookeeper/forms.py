# forms.py
from django import forms
from .models import Animal, Species

class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = ['name', 'species', 'enclosure']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['species'].queryset = Species.objects.all()
