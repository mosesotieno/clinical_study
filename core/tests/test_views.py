# core/tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from core.models import Participant, Visit, Vitals, DoctorQuestionnaire, PsychiatristQuestionnaire, LabRequest


class ViewTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create test participant
        self.participant = Participant.objects.create(
            participant_id='TEST001',
            first_name='John',
            last_name='Doe',
            date_of_birth=date(1990, 1, 1),
            gender='M',
            contact_info='test@example.com',
            created_by=self.user
        )
        
        # Create test visit
        self.visit = Visit.objects.create(
            participant=self.participant,
            visit_type='BASELINE',
            completed=False
        )

    def login_user(self):
        """Helper method to log in user"""
        self.client.login(username='testuser', password='testpass123')


class DashboardViewTests(ViewTestCase):
    def test_dashboard_redirects_if_not_logged_in(self):
        """Test that dashboard redirects to login if not authenticated"""
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_loads_when_logged_in(self):
        """Test dashboard loads successfully for authenticated user"""
        self.login_user()
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/dashboard.html')


class ParticipantViewTests(ViewTestCase):
    def test_enroll_participant_get(self):
        """Test GET request to enroll participant page"""
        self.login_user()
        response = self.client.get(reverse('core:enroll_participant'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/enrollment.html')

    def test_enroll_participant_post_valid(self):
        """Test POST request with valid data to enroll participant"""
        self.login_user()
        data = {
            'participant_id': 'TEST002',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'date_of_birth': '1995-05-15',
            'gender': 'F',
            'contact_info': 'jane@example.com'
        }
        response = self.client.post(reverse('core:enroll_participant'), data)
        
        # Should redirect to dashboard on success
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:dashboard'))
        
        # Check that participant was created
        self.assertTrue(Participant.objects.filter(participant_id='TEST002').exists())


class VisitWorkflowTests(ViewTestCase):
    def test_take_vitals_get(self):
        """Test GET request to take vitals page"""
        self.login_user()
        response = self.client.get(reverse('core:vitals', args=[self.visit.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/vitals.html')

    def test_take_vitals_post_valid(self):
        """Test POST request with valid vitals data"""
        self.login_user()
        data = {
            'blood_pressure_systolic': 120,
            'blood_pressure_diastolic': 80,
            'heart_rate': 72,
            'temperature': 98.6,
            'height': 175.0,
            'weight': 70.0,
        }
        response = self.client.post(reverse('core:vitals', args=[self.visit.id]), data)
        
        # Should redirect to doctor assessment - use the actual URL name from your urls.py
        self.assertEqual(response.status_code, 302)
        
        # Check the redirect URL based on your actual URL pattern
        # If your URL is named 'doctor_assessment' in urls.py
        expected_url = reverse('core:doctor_assessment', args=[self.visit.id])
        self.assertEqual(response.url, expected_url)
        
        # Check that vitals were created
        self.assertTrue(Vitals.objects.filter(visit=self.visit).exists())

    def test_doctor_assessment_requires_vitals(self):
        """Test that doctor assessment redirects if vitals not completed"""
        self.login_user()
        response = self.client.get(reverse('core:doctor_assessment', args=[self.visit.id]))
        
        # Should redirect to vitals page with warning
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:vitals', args=[self.visit.id]))

    def test_doctor_assessment_with_vitals(self):
        """Test doctor assessment when vitals exist"""
        self.login_user()
        
        # Create vitals first
        Vitals.objects.create(
            visit=self.visit,
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            heart_rate=72,
            temperature=98.6,
            height=175.0,
            weight=70.0,
            taken_by=self.user
        )
        
        response = self.client.get(reverse('core:doctor_assessment', args=[self.visit.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/doctor_assessment.html')

    def test_psychiatrist_assessment_requires_doctor(self):
        """Test that psychiatrist assessment redirects if doctor assessment not completed"""
        self.login_user()
        response = self.client.get(reverse('core:psychiatrist_assessment', args=[self.visit.id]))
        
        # Should redirect to doctor assessment
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:doctor_assessment', args=[self.visit.id]))

    def test_complete_visit(self):
        """Test completing a visit"""
        self.login_user()
        response = self.client.post(reverse('core:complete_visit', args=[self.visit.id]))
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:dashboard'))
        
        # Visit should be marked as completed
        self.visit.refresh_from_db()
        self.assertTrue(self.visit.completed)


class APIViewTests(ViewTestCase):
    def test_participant_search(self):
        """Test participant search API"""
        self.login_user()
        response = self.client.get(reverse('core:participant_search') + '?q=TEST')
        self.assertEqual(response.status_code, 200)
        
        # Should return JSON response
        import json
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['participant_id'], 'TEST001')