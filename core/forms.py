from django import forms
from .models import Participant, Vitals, DoctorQuestionnaire, PsychiatristQuestionnaire, LabRequest, Visit


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['participant_id', 'first_name', 'last_name', 'date_of_birth', 'gender', 'contact_info']


class VisitForm(forms.ModelForm):
    # Optional: Add a notes field if you want to capture notes without modifying the model
    visit_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Any special notes for this visit...',
            'class': 'form-control'
        }),
        label="Initial Notes (Optional)"
    )
    
    class Meta:
        model = Visit
        fields = ['visit_type']  # Only include model fields here
        widgets = {
            'visit_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            })
        }
        labels = {
            'visit_type': 'Visit Type *'
        }
    
    def __init__(self, *args, **kwargs):
        # Extract participant before calling super
        self.participant = None
        if 'participant' in kwargs:
            self.participant = kwargs.pop('participant')
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True):
        # Don't call super().save() immediately
        instance = super().save(commit=False)
        if self.participant:
            instance.participant = self.participant
        if commit:
            instance.save()
        return instance

class DoctorQuestionnaireForm(forms.ModelForm):
    class Meta:
        model = DoctorQuestionnaire
        fields = ['chief_complaint', 'medical_history', 'current_medications', 'physical_exam_findings']


class PsychiatristQuestionnaireForm(forms.ModelForm):
    class Meta:
        model = PsychiatristQuestionnaire
        fields = ['mental_status_exam', 'risk_factors', 'recommendations']


class LabRequestForm(forms.ModelForm):
    class Meta:
        model = LabRequest
        fields = ['tests_requested', 'urgency', 'notes']


class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['visit_type']


class DoctorAssessmentForm(forms.ModelForm):
    class Meta:
        model = DoctorQuestionnaire
        fields = [
            "chief_complaint",
            "medical_history",
            "current_medications",
            "physical_exam_findings",
        ]
        widgets = {
            "chief_complaint": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Primary reason for visit..."
            }),
            "medical_history": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Relevant medical history..."
            }),
            "current_medications": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "List current medications..."
            }),
            "physical_exam_findings": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Document physical examination findings..."
            }),
        }