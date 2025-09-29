# models.py
from django.db import models
from django.contrib.auth.models import User

class Participant(models.Model):
    participant_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    contact_info = models.CharField(max_length=100)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"{self.participant_id} - {self.first_name} {self.last_name}"
    
    @property
    def has_active_visit(self):
        """Check if participant has any active visits"""
        return self.visits.filter(completed=False).exists()

class Visit(models.Model):
    VISIT_TYPES = [
        ('BASELINE', 'Baseline Visit'),
        ('FOLLOWUP_1', '1st Follow-up'),
        ('FOLLOWUP_2', '2nd Follow-up'),
    ]
    
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='visits')
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPES)
    visit_date = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

class Vitals(models.Model):
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name='vitals')
    blood_pressure_systolic = models.IntegerField()
    blood_pressure_diastolic = models.IntegerField()
    heart_rate = models.IntegerField()
    temperature = models.DecimalField(max_digits=4, decimal_places=2)
    height = models.DecimalField(max_digits=5, decimal_places=2)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    taken_by = models.ForeignKey(User, on_delete=models.PROTECT)
    taken_at = models.DateTimeField(auto_now_add=True)

class DoctorQuestionnaire(models.Model):
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name='doctor_questionnaire')
    # Add your specific medical questions here
    chief_complaint = models.TextField()
    medical_history = models.TextField()
    current_medications = models.TextField()
    physical_exam_findings = models.TextField()
    completed_by = models.ForeignKey(User, on_delete=models.PROTECT)
    completed_at = models.DateTimeField(auto_now_add=True)

class PsychiatristQuestionnaire(models.Model):
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name='psychiatrist_questionnaire')
    # Add psychiatric assessment fields
    mental_status_exam = models.TextField()
    assessment_notes = models.TextField()
    risk_factors = models.TextField()
    recommendations = models.TextField()
    completed_by = models.ForeignKey(User, on_delete=models.PROTECT)
    completed_at = models.DateTimeField(auto_now_add=True)

class LabRequest(models.Model):
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name='lab_request')
    tests_requested = models.JSONField()  # Store list of tests
    urgency = models.CharField(max_length=20, choices=[
        ('ROUTINE', 'Routine'),
        ('URGENT', 'Urgent'),
        ('STAT', 'Stat')
    ])
    notes = models.TextField(blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT)
    requested_at = models.DateTimeField(auto_now_add=True)