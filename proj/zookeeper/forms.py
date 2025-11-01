from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Animal, Species, Enclosure
from django.core.exceptions import ValidationError

class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = ['name', 'species', 'enclosure']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['species'].queryset = Species.objects.all()
        self.fields['enclosure'].queryset = Enclosure.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        species = cleaned_data.get('species')
        enclosure = cleaned_data.get('enclosure')
        
        if species and enclosure:
            # Check if the enclosure's diet type matches the species' diet
            if species.diet != enclosure.diet_type:
                raise ValidationError(
                    f"This enclosure is designed for {enclosure.get_diet_type_display()} animals, "
                    f"but this species is {species.get_diet_display()}"
                )
            
            # Check if the enclosure is full
            if enclosure.is_full and (not self.instance or self.instance.enclosure != enclosure):
                raise ValidationError(f"This enclosure is already at full capacity ({enclosure.capacity} animals)")
        
        return cleaned_data

class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species
        fields = ['name', 'diet']

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_staff = forms.BooleanField(required=False, label='Staff Status')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'is_staff']

class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(required=True)
    is_staff = forms.BooleanField(required=False, label='Staff Status')

    class Meta:
        model = User
        fields = ['username', 'email', 'is_staff']
        exclude = ['password']

class EnclosureForm(forms.ModelForm):
    class Meta:
        model = Enclosure
        fields = ['name', 'description', 'capacity', 'diet_type']
