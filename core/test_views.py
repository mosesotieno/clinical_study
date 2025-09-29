from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Participant, Visit, Vitals, DoctorQuestionnaire, PsychiatristQuestionnaire, LabRequest


class WorkflowViewTests(TestCase):
    def setUp(self):
        # Client + user
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="pass123")
        self.client.login(username="tester", password="pass123")

        # Base participant + visit
        self.participant = Participant.objects.create(
            participant_id="PX001",
            first_name="Jane",
            last_name="Doe",
            date_of_birth="1990-01-01",
            gender="F",
            contact_info="janedoe@example.com",
            created_by=self.user,
        )
        self.visit = Visit.objects.create(participant=self.participant, visit_type="BASELINE")

    def test_dashboard(self):
        url = reverse("core:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane")

    def test_enroll_participant_post(self):
        url = reverse("core:enroll_participant")
        data = {
            "participant_id": "PX002",
            "first_name": "Mike",
            "last_name": "Smith",
            "date_of_birth": "1985-05-05",
            "gender": "M",
            "contact_info": "mike@example.com",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # redirect after success
        self.assertTrue(Participant.objects.filter(participant_id="PX002").exists())

    def test_take_vitals_post(self):
        url = reverse("core:vitals", args=[self.visit.id])
        data = {
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "heart_rate": 72,
            "temperature": 36.5,
            "height": 170,
            "weight": 65,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # redirect to doctor
        self.assertTrue(Vitals.objects.filter(visit=self.visit).exists())

    def test_doctor_assessment_redirects_if_no_vitals(self):
        url = reverse("core:doctor_assessment", args=[self.visit.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # redirect back to vitals

    def test_full_workflow_post(self):
        """Run through vitals → doctor → psychiatrist → lab → complete"""
        # Add vitals
        self.client.post(reverse("core:vitals", args=[self.visit.id]), {
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "heart_rate": 70,
            "temperature": 37,
            "height": 175,
            "weight": 70,
        })
        self.assertTrue(Vitals.objects.filter(visit=self.visit).exists())

        # Doctor assessment
        self.client.post(reverse("core:doctor_assessment", args=[self.visit.id]), {
            "chief_complaint": "Headache",
            "medical_history": "None",
            "current_medications": "Paracetamol",
            "physical_exam_findings": "Normal",
        })
        self.assertTrue(DoctorQuestionnaire.objects.filter(visit=self.visit).exists())

        # Psychiatrist assessment
        self.client.post(reverse("core:psychiatrist_assessment", args=[self.visit.id]), {
            "mental_status_exam": "Stable",
            "risk_factors": "None",
            "recommendations": "Counseling",
        })
        self.assertTrue(PsychiatristQuestionnaire.objects.filter(visit=self.visit).exists())

        # Lab request
        self.client.post(reverse("core:lab_request", args=[self.visit.id]), {
            "tests_requested": ["Blood Test"],
            "urgency": "Normal",
            "notes": "Routine",
        })
        self.assertTrue(LabRequest.objects.filter(visit=self.visit).exists())

        # Complete visit
        self.client.post(reverse("core:complete_visit", args=[self.visit.id]))
        self.visit.refresh_from_db()
        self.assertTrue(self.visit.completed)

    def test_participant_search_api(self):
        url = reverse("core:participant_search")
        response = self.client.get(url, {"q": "Jane"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Jane", response.json()[0]["name"])

    def test_visit_status_api(self):
        url = reverse("core:visit_status", args=[self.visit.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("completed", response.json())
