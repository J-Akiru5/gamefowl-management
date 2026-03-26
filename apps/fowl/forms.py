"""
Forms for fowl app.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Gamefowl, Bloodline, FowlBloodline


# Common Tailwind classes for form styling
INPUT_CLASS = 'w-full px-4 py-3 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent'
SELECT_CLASS = 'w-full px-4 py-3 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 text-gray-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent'
TEXTAREA_CLASS = 'w-full px-4 py-3 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent'
FILE_CLASS = 'w-full px-4 py-3 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 text-gray-800 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-red-600 file:text-white hover:file:bg-red-700'


class GamefowlForm(forms.ModelForm):
    """Form for creating/editing gamefowl."""

    class Meta:
        model = Gamefowl
        fields = [
            'name', 'wing_band', 'breed', 'gender', 'status',
            'date_of_birth', 'date_of_death',
            'sire', 'dam',
            'weight', 'height', 'leg_color', 'plumage_color',
            'plumage_pattern', 'eye_color', 'comb_type',
            'image', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Enter fowl name',
            }),
            'wing_band': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Wing band ID (optional)',
            }),
            'breed': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Breed classification',
            }),
            'gender': forms.Select(attrs={'class': SELECT_CLASS}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'date_of_birth': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date',
            }),
            'date_of_death': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date',
            }),
            'sire': forms.Select(attrs={'class': SELECT_CLASS}),
            'dam': forms.Select(attrs={'class': SELECT_CLASS}),
            'weight': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Weight in kg',
                'step': '0.01',
            }),
            'height': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Height in cm',
                'step': '0.01',
            }),
            'leg_color': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Leg color',
            }),
            'plumage_color': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Plumage color',
            }),
            'plumage_pattern': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Plumage pattern',
            }),
            'eye_color': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Eye color',
            }),
            'comb_type': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Comb type',
            }),
            'image': forms.FileInput(attrs={'class': FILE_CLASS}),
            'notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'placeholder': 'Additional notes...',
                'rows': 3,
            }),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

        # Filter sire/dam choices
        if owner:
            # Only show fowl owned by this owner or marked breeding
            fowl_qs = Gamefowl.objects.filter(owner=owner)
        else:
            fowl_qs = Gamefowl.objects.all()

        # Sire must be male
        self.fields['sire'].queryset = fowl_qs.filter(gender='male')
        self.fields['sire'].empty_label = "-- Select Sire (Father) --"

        # Dam must be female
        self.fields['dam'].queryset = fowl_qs.filter(gender='female')
        self.fields['dam'].empty_label = "-- Select Dam (Mother) --"

        # Exclude self from sire/dam if editing existing fowl
        if self.instance and self.instance.pk:
            self.fields['sire'].queryset = self.fields['sire'].queryset.exclude(
                pk=self.instance.pk
            )
            self.fields['dam'].queryset = self.fields['dam'].queryset.exclude(
                pk=self.instance.pk
            )

    def clean(self):
        cleaned_data = super().clean()
        sire = cleaned_data.get('sire')
        dam = cleaned_data.get('dam')
        date_of_birth = cleaned_data.get('date_of_birth')
        date_of_death = cleaned_data.get('date_of_death')

        # Validate sire is male
        if sire and sire.gender != 'male':
            raise ValidationError({'sire': 'Sire must be male.'})

        # Validate dam is female
        if dam and dam.gender != 'female':
            raise ValidationError({'dam': 'Dam must be female.'})

        # Validate sire/dam are not the same as the fowl itself
        if self.instance and self.instance.pk:
            if sire and sire.pk == self.instance.pk:
                raise ValidationError({'sire': 'A fowl cannot be its own sire.'})
            if dam and dam.pk == self.instance.pk:
                raise ValidationError({'dam': 'A fowl cannot be its own dam.'})

        # Validate death date is after birth date
        if date_of_birth and date_of_death:
            if date_of_death < date_of_birth:
                raise ValidationError({
                    'date_of_death': 'Date of death cannot be before date of birth.'
                })

        return cleaned_data


class BloodlineForm(forms.ModelForm):
    """Form for creating/editing bloodlines."""

    class Meta:
        model = Bloodline
        fields = ['name', 'origin', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Bloodline name',
            }),
            'origin': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Origin breeder or country',
            }),
            'description': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'placeholder': 'Description of this bloodline...',
                'rows': 3,
            }),
        }


class FowlBloodlineForm(forms.ModelForm):
    """Form for adding/editing a single bloodline percentage."""

    class Meta:
        model = FowlBloodline
        fields = ['bloodline', 'percentage', 'is_manual_override', 'notes']
        widgets = {
            'bloodline': forms.Select(attrs={'class': SELECT_CLASS}),
            'percentage': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Percentage (0-100)',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'is_manual_override': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-gray-300 text-red-600 focus:ring-red-500',
            }),
            'notes': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Notes (optional)',
            }),
        }


class BloodlinePercentageFormSet(forms.BaseInlineFormSet):
    """Formset for managing multiple bloodline percentages."""

    def clean(self):
        """Validate that total percentages sum to approximately 100."""
        super().clean()

        if any(self.errors):
            return

        total = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                total += form.cleaned_data.get('percentage', 0)

        # Allow some tolerance for rounding
        if total > 0 and not (99.5 <= total <= 100.5):
            raise ValidationError(
                f'Bloodline percentages must sum to 100%. Current total: {total}%'
            )


# Inline formset for editing bloodlines on fowl form
FowlBloodlineFormSet = forms.inlineformset_factory(
    Gamefowl,
    FowlBloodline,
    form=FowlBloodlineForm,
    formset=BloodlinePercentageFormSet,
    extra=1,
    can_delete=True,
)


class QuickAddFowlForm(forms.ModelForm):
    """Simplified form for quick adding a fowl."""

    class Meta:
        model = Gamefowl
        fields = ['name', 'gender', 'breed', 'date_of_birth', 'sire', 'dam']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Fowl name',
            }),
            'gender': forms.Select(attrs={'class': SELECT_CLASS}),
            'breed': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Breed',
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date',
            }),
            'sire': forms.Select(attrs={'class': SELECT_CLASS}),
            'dam': forms.Select(attrs={'class': SELECT_CLASS}),
        }
