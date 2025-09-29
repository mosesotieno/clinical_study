from django import forms
from .models import Participant, Vitals, DoctorQuestionnaire, PsychiatristQuestionnaire, LabRequest, Visit



class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = [
            "participant_id",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "contact_info",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }


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
        fields = ["mental_status_exam", "risk_factors", "recommendations"]
        widgets = {
            "mental_status_exam": forms.Textarea(attrs={
                "rows": 4, "class": "form-control",
                "placeholder": "Appearance, behavior, mood, affect, thought process, cognition..."
            }),
            "risk_factors": forms.Textarea(attrs={
                "rows": 3, "class": "form-control",
                "placeholder": "Suicide risk, violence risk, self-harm, etc..."
            }),
            "recommendations": forms.Textarea(attrs={
                "rows": 3, "class": "form-control",
                "placeholder": "Treatment recommendations, follow-up plan..."
            }),
        }


class LabRequestForm(forms.ModelForm):
    TEST_CHOICES = [
        ("CBC", "Complete Blood Count"),
        ("LFT", "Liver Function Test"),
        ("RFT", "Renal Function Test"),
        ("XRAY", "Chest X-Ray"),
        ("HIV", "HIV Test"),
    ]

    tests_requested = forms.MultipleChoiceField(
        choices=TEST_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    class Meta:
        model = LabRequest
        fields = ["tests_requested", "urgency", "notes"]
        widgets = {
            "urgency": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def clean_tests_requested(self):
        """Ensure data is stored as JSON (list)"""
        data = self.cleaned_data["tests_requested"]
        return list(data)  # this will serialize correctly into JSONField


class VitalsForm(forms.ModelForm):
    class Meta:
        model = Vitals
        fields = [
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "heart_rate",
            "temperature",
            "height",
            "weight",
        ]
        widgets = {
            "blood_pressure_systolic": forms.NumberInput(attrs={"class": "form-control", "min": 50, "max": 250}),
            "blood_pressure_diastolic": forms.NumberInput(attrs={"class": "form-control", "min": 30, "max": 150}),
            "heart_rate": forms.NumberInput(attrs={"class": "form-control", "min": 30, "max": 200}),
            "temperature": forms.NumberInput(attrs={"class": "form-control", "step": 0.1, "min": 35, "max": 42}),
            "height": forms.NumberInput(attrs={"class": "form-control", "step": 0.1, "min": 100, "max": 220}),
            "weight": forms.NumberInput(attrs={"class": "form-control", "step": 0.1, "min": 30, "max": 200}),
        }

    def clean(self):
        cleaned_data = super().clean()
        systolic = cleaned_data.get("blood_pressure_systolic")
        diastolic = cleaned_data.get("blood_pressure_diastolic")

        if systolic and diastolic and systolic <= diastolic:
            raise forms.ValidationError("Systolic pressure must be greater than diastolic pressure.")
        return cleaned_data



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