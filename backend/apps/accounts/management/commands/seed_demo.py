from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.applications.models import Application
from apps.assignments.models import Assignment
from apps.complaints.models import Complaint
from apps.fraud.models import FraudAlert
from apps.notifications.models import Notification
from apps.payments.models import Transaction
from apps.profiles.models import ClientProfile, WorkerProfile
from apps.reputation.services import update_reputation
from apps.reviews.models import Review
from apps.skills.models import Skill, WorkerSkill
from apps.tasks.models import Task, TaskSkill


class Command(BaseCommand):
    help = "Create idempotent local demo data for presenting WorkNeuron."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="DemoPass123!",
            help="Password for all demo accounts (default: DemoPass123!).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        users = self._create_users(password)
        skills = self._create_skills()
        self._create_profiles(users)
        self._create_worker_skills(users, skills)
        tasks = self._create_tasks(users, skills)
        self._create_workflows(users, tasks)
        self._create_notifications(users, tasks)
        self._create_admin_demo_data(users, tasks)
        for user in users.values():
            update_reputation(user)
        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write("Client: demo.client@workneuron.local")
        self.stdout.write("Worker: demo.worker@workneuron.local")
        self.stdout.write("Admin: demo.admin@workneuron.local")
        self.stdout.write("Use the password supplied with --password.")

    def _user(self, email, role, password, first_name, last_name):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"role": role, "first_name": first_name, "last_name": last_name},
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user

    def _create_users(self, password):
        admin, created = User.objects.get_or_create(
            email="demo.admin@workneuron.local",
            defaults={"role": User.Role.ADMIN, "first_name": "Asha", "last_name": "Admin", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password(password)
            admin.save(update_fields=["password"])
        return {
            "client": self._user("demo.client@workneuron.local", User.Role.CLIENT, password, "Riya", "Client"),
            "second_client": self._user("sarah.client@workneuron.local", User.Role.CLIENT, password, "Sarah", "Shah"),
            "worker": self._user("demo.worker@workneuron.local", User.Role.WORKER, password, "Arjun", "Kumar"),
            "second_worker": self._user("meera.worker@workneuron.local", User.Role.WORKER, password, "Meera", "Nair"),
            "admin": admin,
        }

    def _create_skills(self):
        catalog = {
            "Python": "Programming",
            "Django": "Programming",
            "React": "Frontend",
            "PostgreSQL": "Database",
            "Data Analysis": "Analytics",
            "UI/UX Design": "Design",
        }
        return {name: Skill.objects.get_or_create(name=name, defaults={"category": category})[0] for name, category in catalog.items()}

    def _create_profiles(self, users):
        ClientProfile.objects.get_or_create(user=users["client"], defaults={"organization_name": "Neuron Labs", "bio": "A product team building useful digital tools.", "location": "Hyderabad", "website": "https://example.com"})
        ClientProfile.objects.get_or_create(user=users["second_client"], defaults={"organization_name": "Insight Studio", "bio": "A data-driven design studio.", "location": "Bengaluru", "website": "https://example.com"})
        WorkerProfile.objects.get_or_create(user=users["worker"], defaults={"headline": "Python and Django developer", "bio": "Builds reliable Django APIs and PostgreSQL-backed applications.", "experience_years": 4, "location": "Remote", "availability": WorkerProfile.Availability.PART_TIME})
        WorkerProfile.objects.get_or_create(user=users["second_worker"], defaults={"headline": "React UI and data specialist", "bio": "Designs accessible React interfaces and analytics dashboards.", "experience_years": 3, "location": "Bengaluru", "availability": WorkerProfile.Availability.FLEXIBLE})

    def _create_worker_skills(self, users, skills):
        for worker, names in ((users["worker"], ("Python", "Django", "PostgreSQL")), (users["second_worker"], ("React", "Data Analysis", "UI/UX Design"))):
            for name in names:
                WorkerSkill.objects.get_or_create(worker=worker, skill=skills[name], defaults={"proficiency": 5 if name in ("Python", "Django", "React") else 4, "years_experience": 4 if worker == users["worker"] else 3})

    def _task(self, owner, title, description, budget, location, skills, status=Task.Status.OPEN):
        task, _ = Task.objects.get_or_create(
            owner=owner,
            title=title,
            defaults={"description": description, "budget": budget, "deadline": timezone.now() + timedelta(days=14), "location": location, "availability_requirements": "Flexible", "status": status},
        )
        if task.status != status:
            task.status = status
            task.save(update_fields=["status", "updated_at"])
        for skill in skills:
            TaskSkill.objects.get_or_create(task=task, skill=skill)
        return task

    def _create_tasks(self, users, skills):
        return {
            "open": self._task(users["client"], "React dashboard refinement", "Improve a responsive React dashboard with accessible components and polished empty states.", "12000.00", "Remote", [skills["React"], skills["UI/UX Design"]]),
            "applications": self._task(users["second_client"], "Data analytics dashboard", "Create a data analysis dashboard with PostgreSQL reporting and clear visual insights.", "18000.00", "Bengaluru", [skills["React"], skills["Data Analysis"], skills["PostgreSQL"]], Task.Status.APPLICATIONS_RECEIVED),
            "assigned": self._task(users["client"], "Django marketplace API", "Build secure Django REST endpoints for a task marketplace using Python and PostgreSQL.", "25000.00", "Remote", [skills["Python"], skills["Django"], skills["PostgreSQL"]], Task.Status.ASSIGNED),
            "completed": self._task(users["second_client"], "Python reporting automation", "Automate weekly business reports with Python and PostgreSQL data exports.", "9000.00", "Remote", [skills["Python"], skills["PostgreSQL"]], Task.Status.COMPLETED),
        }

    def _application(self, task, worker, status, cover_letter):
        application, _ = Application.objects.get_or_create(task=task, worker=worker, defaults={"cover_letter": cover_letter, "status": status})
        if application.status != status:
            application.status = status
            application.save(update_fields=["status", "updated_at"])
        return application

    def _create_workflows(self, users, tasks):
        self._application(tasks["applications"], users["second_worker"], Application.Status.SUBMITTED, "I have built React dashboards and can deliver clear data visualizations.")
        assigned_application = self._application(tasks["assigned"], users["worker"], Application.Status.ACCEPTED, "My Django and PostgreSQL experience fits this marketplace API well.")
        Assignment.objects.get_or_create(task=tasks["assigned"], defaults={"worker": users["worker"], "application": assigned_application, "progress": 35})
        completed_application = self._application(tasks["completed"], users["worker"], Application.Status.ACCEPTED, "I can automate these Python reports reliably.")
        completed_assignment, _ = Assignment.objects.get_or_create(task=tasks["completed"], defaults={"worker": users["worker"], "application": completed_application, "progress": 100, "submission": "Automated reporting scripts and documentation delivered.", "completed_at": timezone.now() - timedelta(days=2)})
        Review.objects.get_or_create(assignment=completed_assignment, reviewer=users["second_client"], reviewed_user=users["worker"], defaults={"rating": 5, "review": "Excellent technical delivery and clear communication."})
        Review.objects.get_or_create(assignment=completed_assignment, reviewer=users["worker"], reviewed_user=users["second_client"], defaults={"rating": 5, "review": "Clear requirements and prompt feedback."})
        Transaction.objects.get_or_create(assignment=completed_assignment, payer=users["second_client"], defaults={"amount": "9000.00", "currency": "INR", "provider": "RAZORPAY_TEST", "provider_order_id": "demo_order_reporting", "provider_payment_id": "demo_payment_reporting", "status": Transaction.Status.VERIFIED})

    def _create_notifications(self, users, tasks):
        entries = (
            (users["worker"], Notification.Kind.TASK_ASSIGNED, "Task assigned", "You were selected for Django marketplace API.", f"/assignments/{tasks['assigned'].id}"),
            (users["second_worker"], Notification.Kind.APPLICATION_RECEIVED, "Application received", "Your application for Data analytics dashboard is awaiting review.", f"/tasks/{tasks['applications'].id}"),
            (users["client"], Notification.Kind.TASK_COMPLETED, "Payment recorded", "A completed demo payment is available in the payment history.", "/payments"),
        )
        for recipient, kind, title, message, related_url in entries:
            Notification.objects.get_or_create(recipient=recipient, kind=kind, title=title, defaults={"message": message, "related_url": related_url})

    def _create_admin_demo_data(self, users, tasks):
        Complaint.objects.get_or_create(complainant=users["second_worker"], category=Complaint.Category.TASK, task=tasks["applications"], defaults={"description": "Demo complaint for the administrator presentation.", "status": Complaint.Status.UNDER_REVIEW})
        FraudAlert.objects.get_or_create(alert_type=FraudAlert.AlertType.HIGH_APPLICATION_ACTIVITY, user=users["worker"], status=FraudAlert.Status.OPEN, defaults={"score": "72.50", "evidence": {"note": "Presentation-only alert based on sample activity."}})
