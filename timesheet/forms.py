from django import forms
from .models import Job, TimeEntry
from django.core.exceptions import ValidationError
from django.utils import timezone

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['name', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }

class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['date', 'start_time', 'end_time', 'break_duration', 'job']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'break_duration': forms.Select(attrs={'class': 'form-control'}),
            'job': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['job'] = forms.ModelChoiceField(
                queryset=Job.objects.filter(user=self.user),
                widget=forms.Select(attrs={'class': 'form-control'})
            )

    def clean(self):
        cleaned_data = super().clean()
        user = self.user
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        job = cleaned_data.get('job')
        if user and date and start_time and end_time:
            overlap = TimeEntry.objects.filter(
                user=user,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if self.instance.pk:
                overlap = overlap.exclude(pk=self.instance.pk)
            if overlap.exists():
                raise ValidationError('Time entry overlaps with an existing entry.')
        if start_time and end_time and start_time >= end_time:
            raise ValidationError('End time must be after start time.')
        return cleaned_data
