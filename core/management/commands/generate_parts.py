import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker
from core.models import Participant

class Command(BaseCommand):
    help = 'Generate realistic fake participants for clinical study'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of participants to create (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing participants before generating new ones'
        )
        parser.add_argument(
            '--age-min',
            type=int,
            default=18,
            help='Minimum age for participants (default: 18)'
        )
        parser.add_argument(
            '--age-max',
            type=int,
            default=80,
            help='Maximum age for participants (default: 80)'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear_existing = options['clear']
        age_min = options['age_min']
        age_max = options['age_max']
        fake = Faker()

        # Get or create a user for created_by field
        user, created = User.objects.get_or_create(
            username='clinical_staff',
            defaults={
                'first_name': 'Clinical',
                'last_name': 'Staff',
                'email': 'staff@clinicalstudy.com',
                'is_staff': True,
                'is_active': True
            }
        )

        if created:
            user.set_password('clinical_staff_123')
            user.save()
            self.stdout.write(
                self.style.SUCCESS('Created clinical staff user for participant generation')
            )

        if clear_existing:
            deleted_count, _ = Participant.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing participants')
            )

        participants_created = 0

        # Common medical conditions for more realistic data
        medical_conditions = [
            "Hypertension", "Diabetes", "Asthma", "Arthritis", "Migraine",
            "Depression", "Anxiety", "High Cholesterol", "Back Pain", "Allergies"
        ]

        for i in range(count):
            try:
                # Generate realistic participant data
                first_name = fake.first_name()
                last_name = fake.last_name()
                date_of_birth = fake.date_of_birth(minimum_age=age_min, maximum_age=age_max)
                
                # Generate unique participant ID with clinical format
                participant_id = f"STD-{fake.unique.random_number(digits=5, fix_len=True)}"
                
                # Gender distribution (more realistic: ~49% M, ~49% F, ~2% O)
                gender_choice = random.choices(
                    ['M', 'F', 'O'],
                    weights=[49, 49, 2]
                )[0]
                
                # Contact info (mix of phone and email)
                if random.random() < 0.7:  # 70% phone, 30% email
                    contact_info = fake.phone_number()
                else:
                    contact_info = fake.email()
                
                # Create participant
                participant = Participant.objects.create(
                    participant_id=participant_id,
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=date_of_birth,
                    gender=gender_choice,
                    contact_info=contact_info,
                    created_by=user
                )
                
                # Add some optional medical history (if your model has this field)
                # This is optional - only if your Participant model has medical_history field
                try:
                    if hasattr(participant, 'medical_history') and random.random() < 0.6:
                        # 60% of participants have some medical history
                        conditions = random.sample(
                            medical_conditions, 
                            random.randint(1, 3)
                        )
                        participant.medical_history = f"Previous conditions: {', '.join(conditions)}"
                        participant.save()
                except AttributeError:
                    pass  # medical_history field doesn't exist
                
                participants_created += 1
                
                if participants_created % 10 == 0:
                    self.stdout.write(
                        f'Created {participants_created} participants...'
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating participant {i+1}: {str(e)}')
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {participants_created} realistic participants'
            )
        )