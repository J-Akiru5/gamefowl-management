"""
Forms for fights app.
"""
from django import forms
from django.utils import timezone
from .models import Fight
from apps.fowl.models import Gamefowl


# Common Tailwind classes
INPUT_CLASS = 'w-full px-4 py-3 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent'
SELECT_CLASS = 'w-full px-4 py-3 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 text-gray-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent'
TEXTAREA_CLASS = 'w-full px-4 py-3 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent'


class FightScheduleForm(forms.ModelForm):
    """Form for scheduling a new fight."""

    class Meta:
        model = Fight
        fields = [
            'fowl', 'event_name', 'arena_name', 'arena_location',
            'scheduled_datetime', 'opponent_name', 'opponent_breed',
            'opponent_weight', 'fowl_weight_at_fight', 'notes'
        ]
        widgets = {
            'fowl': forms.Select(attrs={'class': SELECT_CLASS}),
            'event_name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Derby/Event name (optional)',
            }),
            'arena_name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Arena name',
            }),
            'arena_location': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Arena location/address',
            }),
            'scheduled_datetime': forms.DateTimeInput(attrs={
                'class': INPUT_CLASS,
                'type': 'datetime-local',
            }),
            'opponent_name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Opponent name (optional)',
            }),
            'opponent_breed': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Opponent breed (optional)',
            }),
            'opponent_weight': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Opponent weight in kg',
                'step': '0.01',
            }),
            'fowl_weight_at_fight': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Your fowl weight in kg',
                'step': '0.01',
            }),
            'notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'placeholder': 'Pre-fight notes...',
                'rows': 3,
            }),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter fowl choices by owner
        if owner:
            self.fields['fowl'].queryset = Gamefowl.objects.filter(
                owner=owner,
                status__in=['active', 'breeding']
            )
        else:
            self.fields['fowl'].queryset = Gamefowl.objects.filter(
                status__in=['active', 'breeding']
            )

    def clean_scheduled_datetime(self):
        dt = self.cleaned_data.get('scheduled_datetime')
        if dt and dt < timezone.now():
            raise forms.ValidationError("Cannot schedule a fight in the past.")
        return dt


class FightUpdateForm(forms.ModelForm):
    """Form for updating fight details (before completion)."""

    class Meta:
        model = Fight
        fields = [
            'event_name', 'arena_name', 'arena_location',
            'scheduled_datetime', 'opponent_name', 'opponent_breed',
            'opponent_weight', 'fowl_weight_at_fight', 'notes'
        ]
        widgets = {
            'event_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'arena_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'arena_location': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'scheduled_datetime': forms.DateTimeInput(attrs={
                'class': INPUT_CLASS,
                'type': 'datetime-local',
            }),
            'opponent_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'opponent_breed': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'opponent_weight': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01',
            }),
            'fowl_weight_at_fight': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01',
            }),
            'notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3,
            }),
        }


class FightResultForm(forms.Form):
    """Form for recording fight results."""

    result = forms.ChoiceField(
        choices=Fight.Result.choices,
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    fight_duration_minutes = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Duration in minutes (optional)',
        })
    )
    fowl_weight_at_fight = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=4,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Fowl weight at fight (kg)',
            'step': '0.01',
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': TEXTAREA_CLASS,
            'placeholder': 'Fight notes, performance observations...',
            'rows': 4,
        })
    )


class FightCancelForm(forms.Form):
    """Form for cancelling a fight."""

    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': TEXTAREA_CLASS,
            'placeholder': 'Reason for cancellation (optional)...',
            'rows': 2,
        })
    )


class FightFilterForm(forms.Form):
    """Form for filtering fight list."""

    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + list(Fight.Status.choices),
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    result = forms.ChoiceField(
        required=False,
        choices=[('', 'All Results')] + list(Fight.Result.choices),
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    fowl = forms.ModelChoiceField(
        required=False,
        queryset=Gamefowl.objects.none(),
        empty_label='All Fowl',
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': INPUT_CLASS,
            'type': 'date',
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': INPUT_CLASS,
            'type': 'date',
        })
    )

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        if owner:
            self.fields['fowl'].queryset = Gamefowl.objects.filter(owner=owner)
        else:
            self.fields['fowl'].queryset = Gamefowl.objects.all()
