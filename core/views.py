from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
import csv
from datetime import datetime, timedelta

from .models import *
from .forms import *

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_visit_progress(visit):
    """Calculate progress percentage for a visit (0-4)"""
    progress = 0
    if hasattr(visit, 'vitals'):
        progress += 1
    if hasattr(visit, 'doctor_questionnaire'):
        progress += 1
    if hasattr(visit, 'psychiatrist_questionnaire'):
        progress += 1
    if hasattr(visit, 'lab_request'):
        progress += 1
    return progress


def export_participants_csv(participants, data_types):
    """Helper function to export participants to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="participants_export.csv"'
    
    writer = csv.writer(response)
    
    # Write headers
    headers = ['Participant ID', 'First Name', 'Last Name', 'Date of Birth', 'Gender', 'Enrollment Date']
    if 'vitals' in data_types:
        headers.extend(['Blood Pressure', 'Heart Rate', 'Temperature', 'Height', 'Weight'])
    if 'doctor' in data_types:
        headers.extend(['Chief Complaint', 'Medical History'])
    
    writer.writerow(headers)
    
    # Write data
    for participant in participants:
        row = [
            participant.participant_id,
            participant.first_name,
            participant.last_name,
            participant.date_of_birth,
            participant.get_gender_display(),
            participant.enrollment_date.strftime('%Y-%m-%d'),
        ]
        
        if 'vitals' in data_types:
            # Get latest vitals for participant
            latest_vitals = Vitals.objects.filter(visit__participant=participant).order_by('-taken_at').first()
            if latest_vitals:
                row.extend([
                    f"{latest_vitals.blood_pressure_systolic}/{latest_vitals.blood_pressure_diastolic}",
                    latest_vitals.heart_rate,
                    latest_vitals.temperature,
                    latest_vitals.height,
                    latest_vitals.weight,
                ])
            else:
                row.extend(['', '', '', '', ''])
        
        if 'doctor' in data_types:
            # Get latest doctor assessment
            latest_doctor = DoctorQuestionnaire.objects.filter(visit__participant=participant).order_by('-completed_at').first()
            if latest_doctor:
                row.extend([
                    latest_doctor.chief_complaint[:50] + '...' if len(latest_doctor.chief_complaint) > 50 else latest_doctor.chief_complaint,
                    latest_doctor.medical_history[:50] + '...' if len(latest_doctor.medical_history) > 50 else latest_doctor.medical_history,
                ])
            else:
                row.extend(['', ''])
        
        writer.writerow(row)
    
    return response


# =============================================================================
# DASHBOARD & OVERVIEW VIEWS
# =============================================================================

@login_required
def dashboard(request):
    """Main dashboard view"""
    participants = Participant.objects.all().order_by('-enrollment_date')
    active_visits = Visit.objects.filter(completed=False).select_related('participant')
    
    context = {
        'participants': participants,
        'active_visits': active_visits,
    }
    return render(request, 'core/dashboard.html', context)


# =============================================================================
# PARTICIPANT MANAGEMENT VIEWS
# =============================================================================

@login_required
def enroll_participant(request):
    """Enroll a new participant"""
    if request.method == 'POST':
        try:
            participant_id = request.POST.get('participant_id')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            date_of_birth = request.POST.get('date_of_birth')
            gender = request.POST.get('gender')
            contact_info = request.POST.get('contact_info')
            
            participant = Participant.objects.create(
                participant_id=participant_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                gender=gender,
                contact_info=contact_info,
                created_by=request.user
            )
            
            messages.success(request, 'Participant enrolled successfully!')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error enrolling participant: {str(e)}')
    
    return render(request, 'core/enrollment.html')


@login_required
def participant_list(request):
    """List all participants"""
    participants = Participant.objects.all().order_by('-enrollment_date')
    context = {'participants': participants}
    return render(request, 'core/participant_list.html', context)


@login_required
def participant_detail(request, participant_id):
    """Show participant details and visit history"""
    participant = get_object_or_404(Participant, id=participant_id)
    visits = participant.visits.all().order_by('-visit_date')
    context = {
        'participant': participant,
        'visits': visits
    }
    return render(request, 'core/participant_detail.html', context)


@login_required
def delete_participant(request, participant_id):
    """Delete a participant"""
    participant = get_object_or_404(Participant, id=participant_id)
    if request.method == 'POST':
        participant_id = participant.participant_id
        participant.delete()
        messages.success(request, f'Participant {participant_id} has been deleted.')
        return redirect('core:participant_list')
    return redirect('core:participant_detail', participant_id=participant_id)


# =============================================================================
# VISIT MANAGEMENT VIEWS
# =============================================================================

@login_required
def create_visit(request, participant_id):
    participant = get_object_or_404(Participant, id=participant_id)

    if request.method == "POST":
        form = VisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.participant = participant
            visit.save()
            messages.success(request, f"New {visit.get_visit_type_display()} visit created!")
            return redirect("core:vitals", visit_id=visit.id)
    else:
        form = VisitForm()

    return render(request, "core/create_visit.html", {"form": form, "participant": participant})


@login_required
def active_visits(request):
    """Show all active visits"""
    visits = Visit.objects.filter(completed=False).select_related('participant')
    
    # Calculate statistics for the template
    visits_waiting_vitals = visits.filter(vitals__isnull=True).count()
    visits_waiting_doctor = visits.filter(vitals__isnull=False, doctor_questionnaire__isnull=True).count()
    visits_waiting_psychiatry = visits.filter(doctor_questionnaire__isnull=False, psychiatrist_questionnaire__isnull=True).count()
    visits_waiting_lab = visits.filter(psychiatrist_questionnaire__isnull=False, lab_request__isnull=True).count()
    
    # Today's statistics
    today = timezone.now().date()
    today_visits = Visit.objects.filter(visit_date__date=today).count()
    today_completed = Visit.objects.filter(completed=True, visit_date__date=today).count()
    
    # Add progress to each visit for the template
    for visit in visits:
        visit.progress = calculate_visit_progress(visit)
    
    context = {
        'visits': visits,
        'visits_waiting_vitals': visits_waiting_vitals,
        'visits_waiting_doctor': visits_waiting_doctor,
        'visits_waiting_psychiatry': visits_waiting_psychiatry,
        'visits_waiting_lab': visits_waiting_lab,
        'today_visits': today_visits,
        'today_completed': today_completed,
    }
    return render(request, 'core/active_visits.html', context)


@login_required
def completed_visits(request):
    """Show all completed visits with filtering options"""
    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    visit_type = request.GET.get('visit_type')
    participant_id = request.GET.get('participant_id')
    
    # Start with completed visits
    visits = Visit.objects.filter(completed=True).select_related('participant')
    
    # Apply filters
    if date_from:
        visits = visits.filter(visit_date__gte=date_from)
    if date_to:
        visits = visits.filter(visit_date__lte=date_to)
    if visit_type:
        visits = visits.filter(visit_type=visit_type)
    if participant_id:
        visits = visits.filter(participant__participant_id__icontains=participant_id)
    
    # Order by most recent first
    visits = visits.order_by('-visit_date')
    
    # Calculate statistics
    total_completed = visits.count()
    today = timezone.now().date()
    completed_today = visits.filter(visit_date__date=today).count()
    completed_this_week = visits.filter(visit_date__date__gte=today - timedelta(days=7)).count()
    
    # Get active visits count for completion rate calculation
    active_visits_count = Visit.objects.filter(completed=False).count()
    total_visits_count = total_completed + active_visits_count
    
    # Visit type breakdown
    visit_type_breakdown = visits.values('visit_type').annotate(
        count=Count('id')
    )
    
    # Calculate percentages
    for breakdown in visit_type_breakdown:
        breakdown['percentage'] = (breakdown['count'] * 100.0 / total_completed) if total_completed > 0 else 0
    
    context = {
        'visits': visits,
        'total_completed': total_completed,
        'completed_today': completed_today,
        'completed_this_week': completed_this_week,
        'total_visits_count': total_visits_count,
        'active_visits_count': active_visits_count,
        'visit_type_breakdown': visit_type_breakdown,
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
            'visit_type': visit_type,
            'participant_id': participant_id,
        }
    }
    return render(request, 'core/completed_visits.html', context)

@login_required
def complete_visit(request, visit_id):
    """Mark visit as completed"""
    visit = get_object_or_404(Visit, id=visit_id)

    if request.method == 'POST':
        visit.completed = True
        visit.save()
        messages.success(request, f'Visit completed for {visit.participant}!')
        return redirect('core:dashboard')

    return render(request, 'core/complete_visit.html', {'visit': visit})

# =============================================================================
# VISIT WORKFLOW VIEWS
# =============================================================================

@login_required
def take_vitals(request, visit_id):
    """Take vitals for a visit"""
    visit = get_object_or_404(Visit, id=visit_id)
    
    if request.method == 'POST':
        try:
            blood_pressure_systolic = request.POST.get('blood_pressure_systolic')
            blood_pressure_diastolic = request.POST.get('blood_pressure_diastolic')
            heart_rate = request.POST.get('heart_rate')
            temperature = request.POST.get('temperature')
            height = request.POST.get('height')
            weight = request.POST.get('weight')
            
            vitals = Vitals.objects.create(
                visit=visit,
                blood_pressure_systolic=blood_pressure_systolic,
                blood_pressure_diastolic=blood_pressure_diastolic,
                heart_rate=heart_rate,
                temperature=temperature,
                height=height,
                weight=weight,
                taken_by=request.user
            )
            
            messages.success(request, 'Vitals recorded successfully!')
            return redirect('core:doctor_assessment', visit_id=visit.id)
        except Exception as e:
            messages.error(request, f'Error saving vitals: {str(e)}')
    
    context = {'visit': visit}
    return render(request, 'core/vitals.html', context)


@login_required
def doctor_assessment(request, visit_id):
    """Doctor assessment for a visit"""
    visit = get_object_or_404(Visit, id=visit_id)

    if not hasattr(visit, "vitals"):
        messages.warning(request, "Please complete vitals first.")
        return redirect("core:vitals", visit_id=visit_id)

    # Calculate BMI if vitals exist
    bmi = None
    if hasattr(visit, "vitals") and visit.vitals.height and visit.vitals.weight:
        height_m = visit.vitals.height / 100
        bmi = round(visit.vitals.weight / (height_m * height_m), 1)

    if request.method == "POST":
        form = DoctorAssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.visit = visit
            assessment.completed_by = request.user
            assessment.save()
            messages.success(request, "Doctor assessment completed!")
            return redirect("core:psychiatrist_assessment", visit_id=visit.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = DoctorAssessmentForm()

    context = {
        "visit": visit,
        "bmi": bmi,
        "form": form,
    }
    return render(request, "core/doctor_assessment.html", context)


@login_required
def psychiatrist_assessment(request, visit_id):
    """Psychiatrist assessment for a visit"""
    visit = get_object_or_404(Visit, id=visit_id)
    
    # Check if previous step (doctor assessment) is completed
    if not hasattr(visit, 'doctor_questionnaire'):
        messages.warning(request, 'Please complete doctor assessment first.')
        return redirect('core:doctor_assessment', visit_id=visit_id)
    
    if request.method == 'POST':
        try:
            mental_status_exam = request.POST.get('mental_status_exam')
            risk_factors = request.POST.get('risk_factors')
            recommendations = request.POST.get('recommendations')
            
            psychiatrist_questionnaire = PsychiatristQuestionnaire.objects.create(
                visit=visit,
                mental_status_exam=mental_status_exam,
                risk_factors=risk_factors,
                recommendations=recommendations,
                completed_by=request.user
            )
            
            messages.success(request, 'Psychiatrist assessment completed!')
            return redirect('core:lab_request', visit_id=visit.id)
        except Exception as e:
            messages.error(request, f'Error saving assessment: {str(e)}')
    
    context = {'visit': visit}
    return render(request, 'core/psychiatrist_assessment.html', context)


@login_required
def create_lab_request(request, visit_id):
    """Create lab request for a visit"""
    visit = get_object_or_404(Visit, id=visit_id)
    
    # Check if previous step (psychiatrist assessment) is completed
    if not hasattr(visit, 'psychiatrist_questionnaire'):
        messages.warning(request, 'Please complete psychiatrist assessment first.')
        return redirect('psychiatrist_assessment', visit_id=visit_id)
    
    if request.method == 'POST':
        try:
            tests_requested = request.POST.getlist('tests_requested')
            urgency = request.POST.get('urgency')
            notes = request.POST.get('notes')
            
            lab_request = LabRequest.objects.create(
                visit=visit,
                tests_requested=tests_requested,
                urgency=urgency,
                notes=notes,
                requested_by=request.user
            )
            
            messages.success(request, 'Lab request created successfully!')
            return redirect('complete_visit', visit_id=visit.id)
        except Exception as e:
            messages.error(request, f'Error creating lab request: {str(e)}')
    
    context = {'visit': visit}
    return render(request, 'core/lab_request.html', context)


@login_required
def complete_visit(request, visit_id):
    """Mark visit as completed"""
    visit = get_object_or_404(Visit, id=visit_id)
    
    if request.method == 'POST':
        visit.completed = True
        visit.save()
        messages.success(request, f'Visit completed for {visit.participant}!')
        return redirect('core:dashboard')
    
    context = {'visit': visit}
    return render(request, 'core/complete_visit.html', context)


# =============================================================================
# REPORTING VIEWS
# =============================================================================

@login_required
def study_progress_report(request):
    """Generate study progress report"""
    # Calculate statistics
    total_participants = Participant.objects.count()
    total_visits = Visit.objects.count()
    completed_visits = Visit.objects.filter(completed=True).count()
    active_visits_count = Visit.objects.filter(completed=False).count()
    
    # Visit type distribution
    visit_types = Visit.objects.values('visit_type').annotate(count=Count('id'))
    
    # Weekly enrollment trend (last 8 weeks)
    eight_weeks_ago = datetime.now() - timedelta(weeks=8)
    weekly_enrollment = Participant.objects.filter(
        enrollment_date__gte=eight_weeks_ago
    ).extra({
        'week': "EXTRACT(WEEK FROM enrollment_date)"
    }).values('week').annotate(count=Count('id'))
    
    context = {
        'total_participants': total_participants,
        'total_visits': total_visits,
        'completed_visits': completed_visits,
        'active_visits_count': active_visits_count,
        'visit_types': visit_types,
        'weekly_enrollment': weekly_enrollment,
    }
    return render(request, 'core/study_progress_report.html', context)


@login_required
def visit_summary_report(request):
    """Generate visit summary report"""
    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    visit_type = request.GET.get('visit_type')
    status = request.GET.get('status')
    
    # Filter visits
    visits = Visit.objects.all().select_related('participant')
    
    if date_from:
        visits = visits.filter(visit_date__gte=date_from)
    if date_to:
        visits = visits.filter(visit_date__lte=date_to)
    if visit_type:
        visits = visits.filter(visit_type=visit_type)
    if status == 'completed':
        visits = visits.filter(completed=True)
    elif status == 'active':
        visits = visits.filter(completed=False)
    
    # Calculate statistics
    total_visits = visits.count()
    completed_count = visits.filter(completed=True).count()
    active_count = visits.filter(completed=False).count()
    
    # Visit type summary
    visit_type_summary = visits.values('visit_type').annotate(
        count=Count('id'),
        avg_duration=Avg('vitals__taken_at')  # This would need proper duration calculation
    )
    
    context = {
        'visits': visits,
        'total_visits': total_visits,
        'completed_count': completed_count,
        'active_count': active_count,
        'visit_type_summary': visit_type_summary,
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
            'visit_type': visit_type,
            'status': status,
        }
    }
    return render(request, 'core/visit_summary_report.html', context)


@login_required
def participant_data_export(request):
    """Export participant data"""
    if request.method == 'POST':
        # Get export parameters
        export_format = request.POST.get('format', 'csv')
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')
        data_types = request.POST.getlist('data_types')
        
        # Filter participants based on date range
        participants = Participant.objects.all()
        if date_from:
            participants = participants.filter(enrollment_date__gte=date_from)
        if date_to:
            participants = participants.filter(enrollment_date__lte=date_to)
        
        if export_format == 'csv':
            return export_participants_csv(participants, data_types)
        elif export_format == 'excel':
            # For Excel export, you would use a library like openpyxl
            messages.info(request, 'Excel export feature coming soon. CSV exported instead.')
            return export_participants_csv(participants, data_types)
    
    return render(request, 'core/participant_data_export.html')


# =============================================================================
# API VIEWS
# =============================================================================

@login_required
def participant_search(request):
    """API endpoint for participant search"""
    query = request.GET.get('q', '')
    if query:
        participants = Participant.objects.filter(
            Q(participant_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )[:10]
        results = [
            {
                'id': p.id,
                'participant_id': p.participant_id,
                'name': f'{p.first_name} {p.last_name}',
                'dob': p.date_of_birth.strftime('%Y-%m-%d')
            }
            for p in participants
        ]
        return JsonResponse(results, safe=False)
    return JsonResponse([], safe=False)


@login_required
def visit_status(request, visit_id):
    """API endpoint for visit status"""
    visit = get_object_or_404(Visit, id=visit_id)
    status = {
        'vitals_completed': hasattr(visit, 'vitals'),
        'doctor_completed': hasattr(visit, 'doctor_questionnaire'),
        'psychiatrist_completed': hasattr(visit, 'psychiatrist_questionnaire'),
        'lab_requested': hasattr(visit, 'lab_request'),
        'completed': visit.completed
    }
    return JsonResponse(status)