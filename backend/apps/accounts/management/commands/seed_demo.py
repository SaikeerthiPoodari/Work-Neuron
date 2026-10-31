from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.applications.models import Application
from apps.assignments.models import Assignment, AssignmentLevel, AssignmentLevelTask
from apps.complaints.models import Complaint
from apps.fraud.models import FraudAlert
from apps.employers.models import EmployerVerification
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.payments.models import BankAccount, PaymentMethod, PaymentProfile, PayoutRecord, Transaction
from apps.profiles.models import ClientProfile, WorkerProfile
from apps.reputation.services import update_reputation
from apps.reviews.models import Review
from apps.skills.models import Skill, WorkerSkill, WorkerSkillHistory
from apps.tasks.models import Task, TaskSkill
from apps.network.models import Connection, DirectMessage, Follow, Post, PostComment, PostLike, PostSave
from apps.search.models import SearchEvent


class Command(BaseCommand):
    help = "Create idempotent local demo data for presenting WorkNeuron."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="DemoPass123!",
            help="Password for all demo accounts (default: DemoPass123!).",
        )
        parser.add_argument("--summary-only", action="store_true", help="Print current demo counts without creating data.")

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        self.demo_password = password
        if options.get("summary_only"):
            self._write_summary()
            return
        users = self._create_users(password)
        skills = self._create_skills()
        self._create_profiles(users)
        self._create_worker_skills(users, skills)
        tasks = self._create_tasks(users, skills)
        self._create_workflows(users, tasks)
        self._create_notifications(users, tasks)
        self._create_admin_demo_data(users, tasks)
        self._create_realistic_ecosystem(users, skills)
        self._create_showcase_coverage(users, skills)
        self._create_demo_trackers()
        self._create_payment_profiles(users)
        for user in users.values():
            update_reputation(user)

    def _create_payment_profiles(self, users):
        demo_users = User.objects.filter(email__endswith="@workneuron.local", is_active=True)
        for user in demo_users:
            profile, _ = PaymentProfile.objects.get_or_create(user=user, defaults={"qr_token": f"WN-DEMO-USER-{user.id:06d}"})
            if not profile.qr_token:
                profile.qr_token = f"WN-DEMO-USER-{user.id:06d}"
                profile.save(update_fields=["qr_token", "updated_at"])
            holder = " ".join(filter(None, [user.first_name, user.last_name])) or user.email
            account, _ = BankAccount.objects.get_or_create(user=user, bank_name="WorkNeuron Demo Bank", account_number=f"900000{user.id:06d}", defaults={"holder_name": holder, "ifsc_code": "WNUR0001234", "account_type": "SAVINGS", "upi_id": f"{user.first_name.lower()}{user.id}@workneuron", "is_primary": True, "verification_status": BankAccount.VerificationStatus.DEMO})
            if not account.is_primary:
                account.is_primary = True
                account.verification_status = BankAccount.VerificationStatus.DEMO
                account.save(update_fields=["is_primary", "verification_status", "updated_at"])
            if user.role == User.Role.CLIENT:
                PaymentMethod.objects.get_or_create(user=user, method_type="TEST_CHECKOUT", display_label="WorkNeuron Test Checkout", defaults={"verification_status": "DEMO", "is_primary": True})
        for transaction in Transaction.objects.filter(assignment__worker__in=demo_users, escrow_status=Transaction.EscrowStatus.RELEASED).select_related("assignment__worker"):
            account = BankAccount.objects.filter(user=transaction.assignment.worker, is_primary=True).first()
            if account:
                PayoutRecord.objects.get_or_create(transaction=transaction, defaults={"worker": transaction.assignment.worker, "bank_account": account, "amount": transaction.amount, "status": PayoutRecord.Status.PAID, "provider_reference": f"demo_payout_{transaction.id}"})
        self._write_summary()
        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write("Clients: demo.client@workneuron.local, plus the seeded client directory")
        self.stdout.write("Workers: demo.worker@workneuron.local, plus the seeded worker directory")
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

    def _create_demo_trackers(self):
        """Create a visible two-way tracker for the seeded walkthrough assignments."""
        assignments = Assignment.objects.filter(task__owner__email__endswith="@workneuron.local").select_related("task", "worker").order_by("id")
        for assignment in assignments:
            if assignment.levels.exists():
                continue
            budget = Decimal(assignment.task.budget)
            allocations = [budget * Decimal("0.10"), budget * Decimal("0.20"), budget * Decimal("0.25"), budget * Decimal("0.25"), budget * Decimal("0.20")]
            allocations[-1] += budget - sum(allocations)
            titles = ["Start – Project initiation", "Level 1 – Requirement analysis", "Level 2 – UI design", "Level 3 – Development", "Final – Delivery"]
            for order, (title, amount) in enumerate(zip(titles, allocations), start=1):
                completed = assignment.task.status == Task.Status.COMPLETED or (assignment.task.status == Task.Status.IN_PROGRESS and order == 1)
                level = AssignmentLevel.objects.create(assignment=assignment, order=order, title=title, description=f"WorkNeuron demo milestone for {assignment.task.title}.", requirements="Share the agreed work and evidence with the other party.", payment_amount=amount, status=AssignmentLevel.Status.COMPLETED if completed else AssignmentLevel.Status.CURRENT if order == 1 else AssignmentLevel.Status.LOCKED, reviewed_at=timezone.now() if completed else None)
                checklist = AssignmentLevelTask.objects.create(level=level, title=f"Confirm {title.lower()} deliverable")
                if completed:
                    checklist.is_completed = True
                    checklist.client_completed = True
                    checklist.completed_at = timezone.now() - timedelta(days=1)
                    checklist.client_completed_at = checklist.completed_at
                    checklist.save(update_fields=["is_completed", "client_completed", "completed_at", "client_completed_at"])
            assignment.progress = 100 if assignment.task.status == Task.Status.COMPLETED else 20 if assignment.task.status == Task.Status.IN_PROGRESS else 0
            assignment.worker_started_at = timezone.now() - timedelta(days=2) if assignment.task.status in (Task.Status.IN_PROGRESS, Task.Status.COMPLETED) else None
            assignment.client_started_at = assignment.worker_started_at
            assignment.started_at = assignment.worker_started_at
            assignment.save(update_fields=["progress", "worker_started_at", "client_started_at", "started_at", "updated_at"])
            if assignment.task.status in (Task.Status.ASSIGNED, Task.Status.IN_PROGRESS, Task.Status.COMPLETED):
                transaction, _ = Transaction.objects.get_or_create(assignment=assignment, payer=assignment.task.owner, defaults={"amount": assignment.task.budget, "currency": "INR", "provider": "DEMO_ESCROW", "provider_order_id": f"demo_tracker_order_{assignment.id}"})
                transaction.status = Transaction.Status.VERIFIED
                transaction.escrow_status = Transaction.EscrowStatus.RELEASED if assignment.task.status == Task.Status.COMPLETED else Transaction.EscrowStatus.HELD
                transaction.save(update_fields=["status", "escrow_status", "updated_at"])

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

    def _create_realistic_ecosystem(self, users, skills):
        """Expand the compact walkthrough data into an interconnected presentation community."""
        client_specs = [
            ("anjali.client@workneuron.local", "Anjali", "Reddy", "Spice Route Kitchen", "RESTAURANT", "Madhapur", "A neighborhood restaurant hiring dependable hospitality staff."),
            ("vikram.client@workneuron.local", "Vikram", "Patel", "FreshCart Supermarket", "SUPERMARKET", "Kukatpally", "A growing supermarket serving west Hyderabad."),
            ("nisha.client@workneuron.local", "Nisha", "Varma", "BrightSide Events", "EVENT_ORGANIZER", "Gachibowli", "Event production and festival staffing team."),
            ("imran.client@workneuron.local", "Imran", "Khan", "SwiftDrop Delivery", "DELIVERY_BUSINESS", "Miyapur", "Local delivery operations for restaurants and shops."),
            ("kavya.client@workneuron.local", "Kavya", "Menon", "Madhura Retail Hub", "LOCAL_BUSINESS", "Ameerpet", "Independent retail and customer-support business."),
            ("rohan.client@workneuron.local", "Rohan", "Das", "UrbanFix Services", "COMPANY", "Uppal", "Home maintenance and repair services."),
            ("sneha.client@workneuron.local", "Sneha", "Joshi", "GreenBasket Stores", "STORE", "Dilsukhnagar", "Convenience stores focused on friendly local service."),
            ("faiz.client@workneuron.local", "Faiz", "Ali", "CityLights Festivals", "EVENT_ORGANIZER", "LB Nagar", "Community events, exhibitions, and seasonal festivals."),
        ]
        extra_clients = []
        for index, (email, first, last, business, employer_type, location, bio) in enumerate(client_specs, 3):
            user = self._user(email, User.Role.CLIENT, self.demo_password, first, last)
            extra_clients.append(user)
            ClientProfile.objects.update_or_create(user=user, defaults={"organization_name": business, "bio": bio, "location": location, "phone": f"+91-9000001{index:03d}", "website": "https://example.com", "employer_type": employer_type})
            EmployerVerification.objects.update_or_create(employer=user, defaults={"legal_name": business, "business_name": business, "employer_type": employer_type, "business_address": f"{location}, Hyderabad", "contact_phone": f"+91-9000001{index:03d}", "recruiter_name": f"{first} {last}", "status": EmployerVerification.Status.VERIFIED if index % 3 else EmployerVerification.Status.PENDING, "submitted_at": timezone.now() - timedelta(days=index), "reviewed_at": timezone.now() - timedelta(days=index - 1) if index % 3 else None})
        worker_specs = [
            ("aditya.worker@workneuron.local", "Aditya", "Rao", "Student web assistant", "Kukatpally", 1, WorkerProfile.Availability.PART_TIME, ("React", "UI/UX Design"), "B.Tech student, JNTU Hyderabad"),
            ("bhavana.worker@workneuron.local", "Bhavana", "Goud", "Fresh graduate data assistant", "Ameerpet", 1, WorkerProfile.Availability.FLEXIBLE, ("Data Analysis", "Python"), "B.Com graduate, Osmania University"),
            ("charan.worker@workneuron.local", "Charan", "Naik", "Certified electrician", "Miyapur", 6, WorkerProfile.Availability.FULL_TIME, ("Python", "PostgreSQL"), "ITI Electrical, Government Industrial Training Institute"),
            ("deepa.worker@workneuron.local", "Deepa", "Rani", "Retail sales associate", "Dilsukhnagar", 3, WorkerProfile.Availability.PART_TIME, ("Data Analysis", "UI/UX Design"), "MBA Retail Management"),
            ("eshwar.worker@workneuron.local", "Eshwar", "Babu", "Plumbing and maintenance helper", "Uppal", 5, WorkerProfile.Availability.FULL_TIME, ("Python", "Django"), "ITI Plumbing and Sanitation"),
            ("farah.worker@workneuron.local", "Farah", "Begum", "Event and hospitality assistant", "Madhapur", 2, WorkerProfile.Availability.WEEKENDS, ("UI/UX Design", "React"), "Diploma in Hospitality"),
            ("gautam.worker@workneuron.local", "Gautam", "Yadav", "Delivery executive", "LB Nagar", 2, WorkerProfile.Availability.FULL_TIME, ("Data Analysis", "PostgreSQL"), "Intermediate, Telangana Board"),
            ("harini.worker@workneuron.local", "Harini", "K", "Customer support associate", "Gachibowli", 2, WorkerProfile.Availability.PART_TIME, ("React", "Data Analysis"), "BA Communications"),
            ("irfan.worker@workneuron.local", "Irfan", "Shaikh", "Store inventory assistant", "Kukatpally", 4, WorkerProfile.Availability.FLEXIBLE, ("PostgreSQL", "Data Analysis"), "BBA Operations"),
            ("jyothi.worker@workneuron.local", "Jyothi", "Sharma", "Festival promotion assistant", "Miyapur", 1, WorkerProfile.Availability.WEEKENDS, ("UI/UX Design", "React"), "BA Media Studies"),
            ("kiran.worker@workneuron.local", "Kiran", "M", "Junior Python developer", "Ameerpet", 2, WorkerProfile.Availability.FLEXIBLE, ("Python", "Django"), "MCA graduate"),
            ("lavanya.worker@workneuron.local", "Lavanya", "S", "Part-time kitchen helper", "Dilsukhnagar", 2, WorkerProfile.Availability.PART_TIME, ("Data Analysis", "UI/UX Design"), "Certificate in Food Safety"),
            ("manoj.worker@workneuron.local", "Manoj", "Kumar", "Event setup technician", "Gachibowli", 7, WorkerProfile.Availability.WEEKENDS, ("Django", "PostgreSQL"), "Diploma in Electrical Engineering"),
        ]
        extra_workers = []
        for index, (email, first, last, headline, location, years, availability, skill_names, education) in enumerate(worker_specs, 3):
            user = self._user(email, User.Role.WORKER, self.demo_password, first, last)
            extra_workers.append(user)
            profile, _ = WorkerProfile.objects.update_or_create(user=user, defaults={"headline": headline, "bio": f"{headline} available for reliable local work around {location}.", "experience_years": years, "location": location, "current_city": "Hyderabad", "current_area": location, "current_state": "Telangana", "education": education, "interests": "Learning, community work, and practical projects", "preferred_job_type": "PART_TIME", "preferred_salary": 12000 + (index * 500), "preferred_working_hours": "Flexible day and evening shifts", "availability": availability, "preferred_job_location": location, "preferred_radius_km": 20})
            for skill_name in skill_names:
                WorkerSkill.objects.get_or_create(worker=user, skill=skills[skill_name], defaults={"proficiency": 3 + (index % 3), "years_experience": years})
        all_clients = [users["client"], users["second_client"], *extra_clients]
        all_workers = [users["worker"], users["second_worker"], *extra_workers]

        job_specs = [
            ("Part-time supermarket assistant", "Support shelf stocking, billing support, and customer requests during evening shifts.", "PART_TIME", "DAILY", "Retail", "Kukatpally", ("Data Analysis",), "1200.00"),
            ("Restaurant kitchen helper", "Assist the kitchen team with preparation, cleaning, and safe food handling.", "DAILY_WAGE", "DAILY", "Hospitality", "Madhapur", ("Data Analysis",), "900.00"),
            ("Weekend event assistant", "Help with registration, guest guidance, and venue coordination for weekend events.", "WEEKEND", "DAILY", "Events", "Gachibowli", ("UI/UX Design",), "1500.00"),
            ("Delivery executive", "Deliver meals and parcels across nearby neighborhoods with a reliable two-wheeler.", "FULL_TIME", "MONTHLY", "Delivery", "Miyapur", ("Data Analysis",), "18000.00"),
            ("Electrician required", "Handle residential electrical inspections, fixture installation, and minor repairs.", "CONTRACT", "FIXED", "Skilled Trades", "Uppal", ("Python",), "22000.00"),
            ("Plumbing assistant", "Work with a senior technician on maintenance visits and plumbing repairs.", "FULL_TIME", "MONTHLY", "Skilled Trades", "LB Nagar", ("Django",), "16000.00"),
            ("Data entry operator", "Enter invoices and inventory records accurately using spreadsheet workflows.", "PART_TIME", "HOURLY", "Operations", "Ameerpet", ("Data Analysis", "PostgreSQL"), "250.00"),
            ("Retail sales assistant", "Welcome customers, maintain displays, and support daily store closing.", "PART_TIME", "MONTHLY", "Retail", "Dilsukhnagar", ("UI/UX Design",), "14000.00"),
            ("Festival event staff", "Support seasonal festival stalls, visitor flow, and vendor coordination.", "FESTIVAL", "FIXED", "Events", "Madhapur", ("React",), "7000.00"),
            ("Daily wage construction helper", "Assist the site team with material movement and safe worksite preparation.", "DAILY_WAGE", "DAILY", "Construction", "Kukatpally", ("Python",), "1100.00"),
            ("Customer support executive", "Answer customer questions over phone and chat and maintain issue records.", "FULL_TIME", "MONTHLY", "Customer Support", "Gachibowli", ("React", "Data Analysis"), "24000.00"),
            ("Social media content assistant", "Prepare short posts and simple visual assets for a neighborhood business.", "FREELANCE", "FIXED", "Marketing", "Remote", ("UI/UX Design", "React"), "9000.00"),
            ("Inventory counting associate", "Complete weekly stock counts and report discrepancies to the store manager.", "WEEKEND", "DAILY", "Operations", "Miyapur", ("Data Analysis",), "1300.00"),
            ("Junior Django API developer", "Implement tested REST endpoints under guidance from a senior engineer.", "INTERNSHIP", "MONTHLY", "Software Engineering", "Remote", ("Python", "Django"), "18000.00"),
            ("React landing page freelancer", "Build a responsive landing page with accessible components and clear CTAs.", "FREELANCE", "FIXED", "Software Engineering", "Remote", ("React", "UI/UX Design"), "15000.00"),
            ("Cafe counter associate", "Manage counter orders, digital payments, and customer service during morning shifts.", "PART_TIME", "MONTHLY", "Hospitality", "LB Nagar", ("Data Analysis",), "12500.00"),
            ("Warehouse packing assistant", "Pack outgoing orders, label parcels, and keep the dispatch area organized.", "FULL_TIME", "MONTHLY", "Logistics", "Uppal", ("PostgreSQL",), "17000.00"),
            ("Home appliance technician", "Support appliance installation visits and document service outcomes.", "CONTRACT", "FIXED", "Skilled Trades", "Dilsukhnagar", ("Django",), "20000.00"),
            ("School event coordinator", "Coordinate volunteers, schedules, and parent check-in for a school program.", "EVENT", "FIXED", "Events", "Ameerpet", ("UI/UX Design",), "6000.00"),
            ("Bilingual call center trainee", "Assist customers in Telugu and English while learning support workflows.", "INTERNSHIP", "MONTHLY", "Customer Support", "Madhapur", ("React",), "15000.00"),
            ("Bookkeeping assistant", "Organize receipts and prepare simple weekly expense summaries.", "PART_TIME", "MONTHLY", "Finance", "Gachibowli", ("Data Analysis", "PostgreSQL"), "16000.00"),
            ("Local courier coordinator", "Assign delivery routes and keep customers updated on order status.", "FULL_TIME", "MONTHLY", "Delivery", "Kukatpally", ("Data Analysis",), "21000.00"),
        ]
        ecosystem_tasks = []
        statuses = [Task.Status.OPEN] * 14 + [Task.Status.APPLICATIONS_RECEIVED] * 3 + [Task.Status.ASSIGNED] * 2 + [Task.Status.IN_PROGRESS] * 2 + [Task.Status.COMPLETED]
        for index, (title, description, job_type, salary_type, category, location, skill_names, budget) in enumerate(job_specs):
            owner = all_clients[index % len(all_clients)]
            status = statuses[index]
            remote = location == "Remote"
            task = self._task(owner, title, description, budget, location, [skills[name] for name in skill_names], status=status, vacancies=1 + (index % 3), category=category, job_type=job_type, salary_type=salary_type, work_mode=Task.WorkMode.REMOTE if remote else Task.WorkMode.ONSITE, is_remote=remote, location_city="" if remote else "Hyderabad", location_area="" if remote else location, location_state="Telangana", working_hours="4-8 hours per shift", education_requirement="Relevant experience or willingness to learn", experience_requirement="0-3 years", start_date=(timezone.now() + timedelta(days=2)).date(), end_date=(timezone.now() + timedelta(days=30)).date())
            ecosystem_tasks.append(task)

        for index, task in enumerate(ecosystem_tasks):
            first_worker = all_workers[index % len(all_workers)]
            second_worker = all_workers[(index + 5) % len(all_workers)]
            status = Application.Status.ACCEPTED if task.status in {Task.Status.ASSIGNED, Task.Status.IN_PROGRESS, Task.Status.COMPLETED} else Application.Status.SUBMITTED
            first_application = self._application(task, first_worker, status, f"I am interested in {task.title.lower()} and can contribute dependable local experience.")
            if index % 2 == 0:
                self._application(task, second_worker, Application.Status.SUBMITTED, f"I can bring a practical, customer-focused approach to {task.title.lower()}.")
            if status == Application.Status.ACCEPTED:
                completed = task.status == Task.Status.COMPLETED
                assignment, _ = Assignment.objects.get_or_create(task=task, defaults={"worker": first_worker, "application": first_application, "progress": 100 if completed else 65 if task.status == Task.Status.IN_PROGRESS else 20, "submission": "Demo work submitted for review." if completed else ""})
                if completed:
                    assignment.completed_at = timezone.now() - timedelta(days=4)
                    assignment.submitted_at = timezone.now() - timedelta(days=5)
                    assignment.save(update_fields=["completed_at", "submitted_at", "updated_at"])
                    Review.objects.get_or_create(assignment=assignment, reviewer=task.owner, reviewed_user=first_worker, defaults={"rating": 4, "review": "Reliable work and thoughtful communication."})
                    Review.objects.get_or_create(assignment=assignment, reviewer=first_worker, reviewed_user=task.owner, defaults={"rating": 4, "review": "Clear brief and helpful feedback."})
                    Transaction.objects.get_or_create(assignment=assignment, payer=task.owner, defaults={"amount": task.budget, "currency": "INR", "provider": "RAZORPAY_TEST", "provider_order_id": f"demo_order_{task.id}", "provider_payment_id": f"demo_payment_{task.id}", "status": Transaction.Status.VERIFIED})
                Notification.objects.get_or_create(recipient=first_worker, kind=Notification.Kind.TASK_ASSIGNED, title=f"Demo assignment update: {task.id}", defaults={"message": f"You have an assignment for {task.title}.", "related_url": f"/tasks/{task.id}"})
            Notification.objects.get_or_create(recipient=task.owner, kind=Notification.Kind.APPLICATION_RECEIVED, title=f"New demo application: {task.id}", defaults={"message": f"A worker applied for {task.title}.", "related_url": f"/tasks/{task.id}"})

        for index in range(12):
            requester = all_workers[index % len(all_workers)]
            recipient = all_clients[index % len(all_clients)]
            connection, _ = Connection.objects.get_or_create(requester=requester, recipient=recipient, defaults={"status": Connection.Status.ACCEPTED if index < 8 else Connection.Status.PENDING})
            if index < 8 and connection.status != Connection.Status.ACCEPTED:
                connection.status = Connection.Status.ACCEPTED; connection.save(update_fields=["status", "updated_at"])
            if connection.status == Connection.Status.ACCEPTED:
                DirectMessage.objects.get_or_create(sender=requester, recipient=recipient, body=f"Hello {recipient.first_name}, I would be glad to discuss upcoming work opportunities.")
                DirectMessage.objects.get_or_create(sender=recipient, recipient=requester, body="Thanks for reaching out. I will share the next suitable opportunity.")
        for index, worker in enumerate(all_workers[:8]):
            Follow.objects.get_or_create(follower=worker, following=all_clients[index % len(all_clients)])
            Post.objects.get_or_create(author=worker, title=f"{worker.first_name}'s WorkNeuron update", defaults={"kind": Post.Kind.UPDATE, "body": f"Building experience through reliable local work and learning opportunities in Hyderabad."})

    def _create_showcase_coverage(self, users, skills):
        """Fill every implemented dashboard surface with real, repeatable records."""
        demo_users = list(User.objects.filter(email__endswith="@workneuron.local", is_active=True))
        clients = [user for user in demo_users if user.role == User.Role.CLIENT]
        workers = [user for user in demo_users if user.role == User.Role.WORKER]
        tasks = list(Task.objects.filter(owner__in=clients).order_by("id"))
        now = timezone.now()

        # Give every demo profile complete, fictional presentation data. SVGs are
        # generated locally so the showcase does not depend on an external image host.
        for index, user in enumerate(clients):
            profile, _ = ClientProfile.objects.get_or_create(user=user)
            profile.organization_name = profile.organization_name or f"{user.first_name}'s Demo Ventures"
            profile.bio = profile.bio or "A fictional WorkNeuron demo business creating dependable local opportunities."
            profile.phone = profile.phone or f"+91-90000{10000 + index:05d}"
            profile.bank_account_name = profile.bank_account_name or f"{user.first_name} Business Demo"
            profile.bank_account_number = profile.bank_account_number or f"811000{user.id:06d}"
            profile.bank_ifsc = profile.bank_ifsc or "WNUR0001234"
            profile.upi_id = profile.upi_id or f"{user.first_name.lower()}.business{user.id}@workneuron"
            profile.location = profile.location or "Hyderabad"
            profile.employer_type = profile.employer_type or ClientProfile.EmployerType.LOCAL_BUSINESS
            if not profile.profile_photo:
                profile.profile_photo.save(f"demo-client-{user.id}.svg", ContentFile(self._avatar_svg(user.first_name, "2563eb").encode()), save=False)
            profile.save()
        for index, user in enumerate(workers):
            profile, _ = WorkerProfile.objects.get_or_create(user=user)
            profile.headline = profile.headline or f"{user.first_name}'s independent professional profile"
            profile.bio = profile.bio or "Reliable fictional demo professional available for practical project work."
            profile.education = profile.education or "Professional certification and field training"
            profile.interests = profile.interests or "Community projects, learning, and dependable service"
            profile.languages = profile.languages or ["en", "hi", "te"]
            profile.preferred_job_type = profile.preferred_job_type or WorkerProfile.Availability.PART_TIME
            profile.preferred_salary = profile.preferred_salary or 14000 + index * 750
            profile.preferred_working_hours = profile.preferred_working_hours or "Morning and evening shifts"
            profile.current_city = profile.current_city or "Hyderabad"
            profile.current_state = profile.current_state or "Telangana"
            profile.preferred_job_location = profile.preferred_job_location or profile.current_city
            profile.profile_photo_url = profile.profile_photo_url or ""
            profile.bank_account_name = profile.bank_account_name or f"{user.first_name} Demo"
            profile.bank_account_number = profile.bank_account_number or f"921000{user.id:06d}"
            profile.bank_ifsc = profile.bank_ifsc or "WNUR0001234"
            profile.upi_id = profile.upi_id or f"{user.first_name.lower()}{user.id}@workneuron"
            profile.payout_qr_token = profile.payout_qr_token or f"WN-DEMO-{user.id:06d}"
            if not profile.profile_photo:
                profile.profile_photo.save(f"demo-worker-{user.id}.svg", ContentFile(self._avatar_svg(user.first_name, "0f766e").encode()), save=False)
            profile.save()
            for skill_index, skill in enumerate(skills.values()):
                if skill_index % 2 == index % 2:
                    current = 3 + ((index + skill_index) % 3)
                    record, _ = WorkerSkill.objects.get_or_create(worker=user, skill=skill, defaults={"proficiency": current, "years_experience": max(1, index % 6)})
                    for step, proficiency in enumerate(sorted({max(1, current - 2), max(1, current - 1), current})):
                        if not WorkerSkillHistory.objects.filter(worker=user, skill=skill, proficiency=proficiency).exists():
                            history = WorkerSkillHistory.objects.create(worker=user, skill=skill, proficiency=proficiency, years_experience=max(0, (index % 6) - 1 + step))
                            history.recorded_at = now - timedelta(days=(3 - step) * 30 + index)
                            history.save(update_fields=["recorded_at"])

        # Keep the presentation contract predictable: every demo client owns at
        # least five jobs, while retaining a mix of lifecycle states.
        showcase_statuses = [Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED]
        for client_index, client in enumerate(clients):
            existing = list(Task.objects.filter(owner=client).order_by("id"))
            for offset in range(len(existing), 5):
                title = f"{client.first_name} demo opportunity {offset + 1}"
                self._task(client, title, f"A fictional {client.first_name} business opportunity for the WorkNeuron presentation.", str(8000 + (client_index * 500) + offset * 750), "Hyderabad", [list(skills.values())[offset % len(skills)]], status=showcase_statuses[(client_index + offset) % len(showcase_statuses)], category="Demo Operations", job_type=Task.JobType.PART_TIME, salary_type=Task.SalaryType.FIXED, work_mode=Task.WorkMode.ONSITE, is_remote=False, location_city="Hyderabad", location_state="Telangana", working_hours="Flexible demo hours", start_date=(now + timedelta(days=2)).date(), end_date=(now + timedelta(days=30)).date())
        tasks = list(Task.objects.filter(owner__in=clients).order_by("id"))

        # Eight applications per worker, with real persisted status diversity.
        application_statuses = [Application.Status.SUBMITTED, Application.Status.REJECTED, Application.Status.ACCEPTED, Application.Status.WITHDRAWN]
        for worker_index, worker in enumerate(workers):
            for offset, task in enumerate(tasks[:8]):
                if task.owner_id == worker.id:
                    continue
                Application.objects.get_or_create(
                    task=task,
                    worker=worker,
                    defaults={
                        "cover_letter": f"Demo application from {worker.first_name} for {task.title}.",
                        "proposed_budget": task.budget,
                        "status": application_statuses[(worker_index + offset) % len(application_statuses)],
                    },
                )

        # Network records are actual relationships, not frontend placeholders.
        network_users = clients + workers
        for index, user in enumerate(network_users):
            target = network_users[(index + 1) % len(network_users)]
            Follow.objects.get_or_create(follower=user, following=target)
            if index % 3 == 0:
                Follow.objects.get_or_create(follower=target, following=user)
            connection, _ = Connection.objects.get_or_create(requester=user, recipient=target, defaults={"status": Connection.Status.ACCEPTED if index % 3 else Connection.Status.PENDING})
            if index % 3 == 1 and connection.status != Connection.Status.ACCEPTED:
                connection.status = Connection.Status.ACCEPTED
                connection.save(update_fields=["status", "updated_at"])
            if connection.status == Connection.Status.ACCEPTED:
                DirectMessage.objects.get_or_create(sender=user, recipient=target, body=f"Demo conversation about {target.first_name}'s next WorkNeuron opportunity.")

            post, _ = Post.objects.get_or_create(author=user, title=f"{user.first_name}'s professional milestone", defaults={"kind": Post.Kind.ACHIEVEMENT if index % 2 else Post.Kind.UPDATE, "body": f"{user.first_name} is building meaningful progress through WorkNeuron projects. #WorkNeuron #Demo"})
            for liker in network_users[(index + 1):(index + 4)]:
                if liker != user:
                    PostLike.objects.get_or_create(post=post, user=liker)
                    PostSave.objects.get_or_create(post=post, user=liker)
            commenter = network_users[(index + 2) % len(network_users)]
            if commenter != user:
                PostComment.objects.get_or_create(post=post, author=commenter, body=f"Great progress, {user.first_name}!")

        # Historical search/activity events make admin and recommendation trends meaningful.
        for index, worker in enumerate(workers):
            for offset, task in enumerate(tasks[:5]):
                if not SearchEvent.objects.filter(user=worker, task=task, kind=SearchEvent.Kind.VIEW).exists():
                    event = SearchEvent.objects.create(user=worker, task=task, kind=SearchEvent.Kind.VIEW, language="en", confidence="0.9200")
                    event.created_at = now - timedelta(days=offset + index + 1)
                    event.save(update_fields=["created_at"])

        # Pending ledger rows complement the verified transactions created by workflows.
        for assignment in Assignment.objects.filter(task__owner__in=clients).select_related("task"):
            if not Transaction.objects.filter(assignment=assignment).exists() and assignment.task.status != Task.Status.CANCELLED:
                Transaction.objects.create(assignment=assignment, payer=assignment.task.owner, amount=assignment.task.budget, currency="INR", provider="RAZORPAY_TEST", provider_order_id=f"demo_pending_order_{assignment.id}", status=Transaction.Status.CREATED)
            elif assignment.task.status == Task.Status.COMPLETED:
                Transaction.objects.filter(assignment=assignment, status=Transaction.Status.VERIFIED).update(escrow_status=Transaction.EscrowStatus.RELEASED)

        for index, user in enumerate(network_users):
            recipient = clients[index % len(clients)]
            Notification.objects.get_or_create(recipient=user, kind=Notification.Kind.MESSAGE_RECEIVED, title="Demo activity update", defaults={"message": f"{recipient.first_name} has new WorkNeuron activity for you to review.", "related_url": "/feed"})

    @staticmethod
    def _avatar_svg(name, color):
        initial = (name or "D")[0].upper()
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" rx="128" fill="#{color}"/><text x="128" y="150" text-anchor="middle" font-family="Arial" font-size="112" font-weight="700" fill="white">{initial}</text></svg>'

    def _write_summary(self):
        demo = User.objects.filter(email__endswith="@workneuron.local")
        self.stdout.write("Demo counts: " + ", ".join([
            f"users={demo.count()}",
            f"clients={demo.filter(role=User.Role.CLIENT).count()}",
            f"workers={demo.filter(role=User.Role.WORKER).count()}",
            f"jobs={Task.objects.filter(owner__in=demo).count()}",
            f"applications={Application.objects.filter(task__owner__in=demo).count()}",
            f"connections={Connection.objects.filter(requester__in=demo, recipient__in=demo).count()}",
            f"posts={Post.objects.filter(author__in=demo).count()}",
            f"likes={PostLike.objects.filter(user__in=demo).count()}",
            f"comments={PostComment.objects.filter(author__in=demo).count()}",
            f"notifications={Notification.objects.filter(recipient__in=demo).count()}",
            f"payments={Transaction.objects.filter(payer__in=demo).count()}",
            f"reviews={Review.objects.filter(reviewer__in=demo).count()}",
        ]))
