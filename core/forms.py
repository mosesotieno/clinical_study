from django import forms
from .models import Participant, Vitals, DoctorQuestionnaire, PsychiatristQuestionnaire, LabRequest, Visit


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['participant_id', 'first_name', 'last_name', 'date_of_birth', 'gender', 'contact_info']


class VitalsForm(forms.ModelForm):
    class Meta:
        model = Vitals
        fields = ['blood_pressure_systolic', 'blood_pressure_diastolic',
                  'heart_rate', 'temperature', 'height', 'weight']


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
