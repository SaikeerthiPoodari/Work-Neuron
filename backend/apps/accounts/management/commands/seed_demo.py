from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.applications.models import Application
from apps.assignments.models import Assignment
from apps.complaints.models import Complaint
from apps.fraud.models import FraudAlert
from apps.employers.models import EmployerVerification
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
        worker, _ = WorkerProfile.objects.get_or_create(user=users["worker"], defaults={"headline": "Python and Django developer", "bio": "Builds reliable Django APIs and PostgreSQL-backed applications.", "experience_years": 4, "location": "Hyderabad", "current_city": "Hyderabad", "current_area": "LB Nagar", "current_state": "Telangana", "latitude": "17.3457", "longitude": "78.5522", "preferred_radius_km": 25, "preferred_job_location": "Hyderabad", "availability": WorkerProfile.Availability.PART_TIME})
        worker.current_city, worker.current_area, worker.current_state = "Hyderabad", "LB Nagar", "Telangana"
        worker.latitude, worker.longitude, worker.preferred_radius_km, worker.preferred_job_location = "17.3457", "78.5522", 25, "Hyderabad"
        worker.save(update_fields=["current_city", "current_area", "current_state", "latitude", "longitude", "preferred_radius_km", "preferred_job_location"])
        second, _ = WorkerProfile.objects.get_or_create(user=users["second_worker"], defaults={"headline": "React UI and data specialist", "bio": "Designs accessible React interfaces and analytics dashboards.", "experience_years": 3, "location": "Bengaluru", "current_city": "Bengaluru", "current_area": "Indiranagar", "current_state": "Karnataka", "latitude": "12.9716", "longitude": "77.5946", "preferred_radius_km": 25, "preferred_job_location": "Bengaluru", "availability": WorkerProfile.Availability.FLEXIBLE})
        second.current_city, second.current_area, second.current_state = "Bengaluru", "Indiranagar", "Karnataka"
        second.latitude, second.longitude, second.preferred_radius_km, second.preferred_job_location = "12.9716", "77.5946", 25, "Bengaluru"
        second.save(update_fields=["current_city", "current_area", "current_state", "latitude", "longitude", "preferred_radius_km", "preferred_job_location"])
        EmployerVerification.objects.update_or_create(employer=users["client"], defaults={"legal_name": "Neuron Labs Private Limited", "business_name": "Neuron Labs", "employer_type": "COMPANY", "business_address": "HITEC City, Hyderabad", "contact_phone": "+91-9000000001", "recruiter_name": "Riya Client", "status": EmployerVerification.Status.VERIFIED, "reviewed_at": timezone.now()})
        EmployerVerification.objects.update_or_create(employer=users["second_client"], defaults={"legal_name": "Insight Studio", "business_name": "Insight Studio", "employer_type": "LOCAL_BUSINESS", "business_address": "Koramangala, Bengaluru", "contact_phone": "+91-9000000002", "recruiter_name": "Sarah Shah", "status": EmployerVerification.Status.PENDING, "submitted_at": timezone.now()})

    def _create_worker_skills(self, users, skills):
        for worker, names in ((users["worker"], ("Python", "Django", "PostgreSQL")), (users["second_worker"], ("React", "Data Analysis", "UI/UX Design"))):
            for name in names:
                WorkerSkill.objects.get_or_create(worker=worker, skill=skills[name], defaults={"proficiency": 5 if name in ("Python", "Django", "React") else 4, "years_experience": 4 if worker == users["worker"] else 3})

    def _task(self, owner, title, description, budget, location, skills, status=Task.Status.OPEN, **extra):
        task, _ = Task.objects.get_or_create(
            owner=owner,
            title=title,
            defaults={"description": description, "budget": budget, "deadline": timezone.now() + timedelta(days=14), "location": location, "availability_requirements": "Flexible", "status": status, **extra},
        )
        changed = []
        for field, value in {"status": status, **extra}.items():
            if getattr(task, field) != value:
                setattr(task, field, value); changed.append(field)
        if changed:
            changed.append("updated_at"); task.save(update_fields=changed)
        for skill in skills:
            TaskSkill.objects.get_or_create(task=task, skill=skill)
        return task

    def _create_tasks(self, users, skills):
        return {
            "open": self._task(users["client"], "React dashboard refinement", "Improve a responsive React dashboard with accessible components and polished empty states.", "12000.00", "Remote", [skills["React"], skills["UI/UX Design"]], work_mode=Task.WorkMode.REMOTE, is_remote=True, job_type=Task.JobType.FREELANCE, salary_type=Task.SalaryType.FIXED, category="Design"),
            "applications": self._task(users["second_client"], "Data analytics dashboard", "Create a data analysis dashboard with PostgreSQL reporting and clear visual insights.", "18000.00", "Bengaluru", [skills["React"], skills["Data Analysis"], skills["PostgreSQL"]], Task.Status.APPLICATIONS_RECEIVED, work_mode=Task.WorkMode.ONSITE, location_city="Bengaluru", location_area="Koramangala", location_state="Karnataka", latitude="12.9352", longitude="77.6245", job_type=Task.JobType.FULL_TIME, salary_type=Task.SalaryType.MONTHLY, category="Data & Analytics"),
            "assigned": self._task(users["client"], "Django marketplace API", "Build secure Django REST endpoints for a task marketplace using Python and PostgreSQL.", "25000.00", "Remote", [skills["Python"], skills["Django"], skills["PostgreSQL"]], Task.Status.ASSIGNED, work_mode=Task.WorkMode.REMOTE, is_remote=True, job_type=Task.JobType.CONTRACT, salary_type=Task.SalaryType.FIXED, category="Software Engineering"),
            "completed": self._task(users["second_client"], "Python reporting automation", "Automate weekly business reports with Python and PostgreSQL data exports.", "9000.00", "Remote", [skills["Python"], skills["PostgreSQL"]], Task.Status.COMPLETED, work_mode=Task.WorkMode.REMOTE, is_remote=True, job_type=Task.JobType.FREELANCE, salary_type=Task.SalaryType.FIXED, category="Data & Analytics"),
            "part_time": self._task(users["client"], "Part-time store assistant", "Support inventory and customer requests at a local store.", "800.00", "LB Nagar, Hyderabad", [skills["Data Analysis"]], work_mode=Task.WorkMode.ONSITE, location_city="Hyderabad", location_area="LB Nagar", location_state="Telangana", latitude="17.3450", longitude="78.5520", job_type=Task.JobType.PART_TIME, salary_type=Task.SalaryType.DAILY, category="Retail"),
            "weekend": self._task(users["client"], "Weekend event coordinator", "Help coordinate guest registration and event logistics.", "1500.00", "Banjara Hills, Hyderabad", [skills["UI/UX Design"]], work_mode=Task.WorkMode.ONSITE, location_city="Hyderabad", location_area="Banjara Hills", location_state="Telangana", latitude="17.4156", longitude="78.4347", job_type=Task.JobType.WEEKEND, salary_type=Task.SalaryType.DAILY, category="Events"),
            "festival": self._task(users["second_client"], "Festival promotion assistant", "Support a seasonal local festival promotion campaign.", "6000.00", "Bengaluru", [skills["React"]], work_mode=Task.WorkMode.HYBRID, location_city="Bengaluru", location_area="Indiranagar", location_state="Karnataka", latitude="12.9784", longitude="77.6408", job_type=Task.JobType.FESTIVAL, salary_type=Task.SalaryType.FIXED, category="Marketing"),
            "internship": self._task(users["client"], "Python data internship", "Assist with data cleanup and reporting automation under mentorship.", "10000.00", "Hyderabad", [skills["Python"], skills["Data Analysis"]], work_mode=Task.WorkMode.HYBRID, location_city="Hyderabad", location_area="HITEC City", location_state="Telangana", latitude="17.4483", longitude="78.3915", job_type=Task.JobType.INTERNSHIP, salary_type=Task.SalaryType.MONTHLY, category="Data & Analytics"),
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
        Complaint.objects.get_or_create(complainant=users["worker"], category=Complaint.Category.JOB_REPORT, task=tasks["festival"], defaults={"report_reason": Complaint.ReportReason.SCAM, "description": "Demo scam/payment concern for moderation review.", "status": Complaint.Status.OPEN})
        FraudAlert.objects.get_or_create(alert_type=FraudAlert.AlertType.HIGH_APPLICATION_ACTIVITY, user=users["worker"], status=FraudAlert.Status.OPEN, defaults={"score": "72.50", "evidence": {"note": "Presentation-only alert based on sample activity."}})
