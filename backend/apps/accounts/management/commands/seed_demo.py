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
        self._create_india_jobs(users["client"], skills)
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
            "Delivery Operations": "Logistics", "Customer Service": "Customer Support",
            "Point of Sale": "Retail", "Sales": "Marketing", "Canva": "Design",
            "HTML": "Programming", "CSS": "Programming", "JavaScript": "Programming",
            "Tutoring": "Education", "Electrical Repair": "Trades", "Plumbing": "Trades",
            "Driving": "Transport", "Photography": "Creative", "Content Writing": "Writing",
            "Housekeeping": "Facilities", "Event Coordination": "Events",
            "Bookkeeping": "Finance", "Data Entry": "Administration", "Inventory": "Retail",
            "Food Safety": "Hospitality", "Tailoring": "Crafts", "Mobile Repair": "Trades",
            "Digital Marketing": "Marketing", "First Aid": "Healthcare", "Translation": "Languages",
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

    def _create_india_jobs(self, owner, skills):
        """Seed a varied, idempotent India-wide job feed with usable map coordinates."""
        cities = {
            "Hyderabad": ("Telangana", [
                ("Gachibowli", 17.4401, 78.3489), ("Madhapur", 17.4510, 78.3860),
                ("Kondapur", 17.4604, 78.3568), ("Kukatpally", 17.4849, 78.4138),
                ("Jubilee Hills", 17.4326, 78.4071), ("Ameerpet", 17.4375, 78.4483),
                ("Begumpet", 17.4448, 78.4663), ("Uppal", 17.4058, 78.5591),
                ("Miyapur", 17.4968, 78.3566), ("Manikonda", 17.4055, 78.3570),
                ("Nallagandla", 17.4753, 78.3138), ("Secunderabad", 17.4399, 78.4983),
            ]),
            "Bengaluru": ("Karnataka", [("Koramangala",12.9352,77.6245),("Whitefield",12.9698,77.7500),("Indiranagar",12.9784,77.6408),("Jayanagar",12.9250,77.5838),("Yeshwanthpur",13.0285,77.5400),("Electronic City",12.8452,77.6602)]),
            "Pune": ("Maharashtra", [("Hinjawadi",18.5913,73.7389),("Kothrud",18.5074,73.8077),("Viman Nagar",18.5679,73.9143),("Hadapsar",18.5089,73.9260),("Baner",18.5590,73.7868),("Shivajinagar",18.5308,73.8475)]),
            "Chennai": ("Tamil Nadu", [("Adyar",13.0012,80.2565),("Guindy",13.0067,80.2206),("Velachery",12.9750,80.2212),("Anna Nagar",13.0850,80.2101),("Tambaram",12.9249,80.1000),("T. Nagar",13.0418,80.2341)]),
            "Mumbai": ("Maharashtra", [("Andheri",19.1197,72.8468),("Bandra",19.0596,72.8295),("Powai",19.1176,72.9060),("Dadar",19.0178,72.8478),("Navi Mumbai",19.0330,73.0297)]),
            "Delhi": ("Delhi", [("Connaught Place",28.6315,77.2167),("Dwarka",28.5921,77.0460),("Rohini",28.7495,77.0565),("Saket",28.5245,77.2066),("Karol Bagh",28.6514,77.1907)]),
            "Kochi": ("Kerala", [("Kakkanad",10.0159,76.3419),("Edappally",10.0261,76.3125),("Fort Kochi",9.9658,76.2421),("Aluva",10.1076,76.3516)]),
            "Coimbatore": ("Tamil Nadu", [("Gandhipuram",11.0168,76.9558),("Peelamedu",11.0280,77.0190),("RS Puram",11.0046,76.9460),("Saravanampatti",11.0800,76.9950)]),
            "Gurugram": ("Haryana", [("Cyber City",28.4950,77.0895),("Sohna Road",28.4180,77.0430),("Sector 14",28.4698,77.0640),("Manesar",28.3670,76.9360)]),
            "Noida": ("Uttar Pradesh", [("Sector 18",28.5708,77.3261),("Sector 62",28.6270,77.3720),("Sector 125",28.5390,77.3330),("Greater Noida",28.4744,77.5040)]),
            "Kolkata": ("West Bengal", [("Salt Lake",22.5867,88.4172),("New Town",22.5800,88.4600),("Park Street",22.5535,88.3520),("Howrah",22.5958,88.2636)]),
            "Visakhapatnam": ("Andhra Pradesh", [("MVP Colony",17.7390,83.3160),("Dwaraka Nagar",17.7280,83.3050),("Gajuwaka",17.7000,83.2160),("Madhurawada",17.8240,83.3540)]),
            "Jaipur": ("Rajasthan", [("Malviya Nagar",26.8540,75.8240),("Vaishali Nagar",26.9120,75.7350),("Mansarovar",26.8550,75.7640)]),
            "Ahmedabad": ("Gujarat", [("Navrangpura",23.0395,72.5610),("Prahlad Nagar",23.0120,72.5100),("Maninagar",22.9960,72.6000)]),
            "Vijayawada": ("Andhra Pradesh", [("Benz Circle",16.4970,80.6570),("Governorpet",16.5190,80.6260),("Poranki",16.4710,80.7130)]),
            "Lucknow": ("Uttar Pradesh", [("Gomti Nagar",26.8490,81.0080),("Hazratganj",26.8500,80.9460),("Aliganj",26.8890,80.9460)]),
            "Indore": ("Madhya Pradesh", [("Vijay Nagar",22.7533,75.8937),("Palasia",22.7250,75.8830),("Rau",22.6380,75.8070)]),
            "Bhubaneswar": ("Odisha", [("Patia",20.3540,85.8190),("Saheed Nagar",20.2960,85.8470),("Khandagiri",20.2590,85.7840)]),
            "Chandigarh": ("Chandigarh", [("Sector 17",30.7410,76.7820),("Sector 22",30.7330,76.7730),("Industrial Area",30.7060,76.8020)]),
            "Guwahati": ("Assam", [("Dispur",26.1430,91.7898),("Paltan Bazaar",26.1780,91.7530),("Six Mile",26.1260,91.8060)]),
            "Mysuru": ("Karnataka", [("Vijayanagar",12.3375,76.6150),("Hebbal",12.3500,76.6400)]),
            "Nagpur": ("Maharashtra", [("Dharampeth",21.1430,79.0580),("Sitabuldi",21.1480,79.0850)]),
            "Surat": ("Gujarat", [("Adajan",21.1950,72.7930),("Vesu",21.1450,72.7700)]),
            "Thiruvananthapuram": ("Kerala", [("Technopark",8.5560,76.8810),("Kowdiar",8.5240,76.9660)]),
            "Patna": ("Bihar", [("Boring Road",25.6100,85.1050),("Kankarbagh",25.5940,85.1580)]),
        }
        # Existing demo workflow tasks already account for these city totals.
        counts = {"Hyderabad": 12, "Bengaluru": 6, "Pune": 6, "Chennai": 6, "Mumbai": 5, "Delhi": 5,
                  "Kochi": 4, "Coimbatore": 4, "Gurugram": 4, "Noida": 4, "Kolkata": 4,
                  "Visakhapatnam": 4, "Jaipur": 3, "Ahmedabad": 3, "Vijayawada": 3, "Lucknow": 3,
                  "Indore": 3, "Bhubaneswar": 3, "Chandigarh": 3, "Guwahati": 3,
                  "Mysuru": 2, "Nagpur": 2, "Surat": 2, "Thiruvananthapuram": 2, "Patna": 2}
        offerings = [
            ("Last-mile delivery partner", "Delivery", "DAILY_WAGE", "DAILY", "Delivery Operations", "2"),
            ("Part-time data entry assistant", "Data Entry", "PART_TIME", "HOURLY", "Data Entry", "1"),
            ("Customer care associate", "Customer Support", "FULL_TIME", "MONTHLY", "Customer Service", "2"),
            ("Retail store associate", "Retail", "PART_TIME", "DAILY", "Point of Sale", "1"),
            ("Local brand promoter", "Marketing", "TEMPORARY", "DAILY", "Sales", "1"),
            ("Small business social creatives", "Graphic Design", "FREELANCE", "FIXED", "Canva", "2"),
            ("Business website refresh", "Web Development", "CONTRACT", "FIXED", "JavaScript", "3"),
            ("After-school maths tutor", "Tutoring", "PART_TIME", "HOURLY", "Tutoring", "2"),
            ("Residential electrician", "Electrician", "DAILY_WAGE", "DAILY", "Electrical Repair", "2"),
            ("Apartment plumbing technician", "Plumber", "TEMPORARY", "DAILY", "Plumbing", "2"),
            ("School route driver", "Driver", "FULL_TIME", "MONTHLY", "Driving", "2"),
            ("Product and event photographer", "Photography", "FREELANCE", "FIXED", "Photography", "2"),
            ("Regional content writer", "Content Writing", "CONTRACT", "FIXED", "Content Writing", "2"),
            ("Office housekeeping crew member", "Housekeeping", "FULL_TIME", "MONTHLY", "Housekeeping", "1"),
            ("Weekend event registration crew", "Event Work", "EVENT", "DAILY", "Event Coordination", "1"),
            ("Small firm accounts assistant", "Accounting", "PART_TIME", "MONTHLY", "Bookkeeping", "2"),
            ("Neighborhood mobile repair technician", "Mobile Repair", "FREELANCE", "FIXED", "Mobile Repair", "3"),
            ("Restaurant kitchen helper", "Hospitality", "WEEKEND", "DAILY", "Food Safety", "1"),
            ("Garment alterations tailor", "Tailoring", "FREELANCE", "FIXED", "Tailoring", "2"),
            ("Bilingual customer help desk", "Customer Support", "PART_TIME", "HOURLY", "Translation", "2"),
            ("Online campaign coordinator", "Digital Marketing", "INTERNSHIP", "MONTHLY", "Digital Marketing", "1"),
            ("Warehouse inventory checker", "Logistics", "TEMPORARY", "DAILY", "Inventory", "1"),
            ("Frontend landing page developer", "Web Development", "FREELANCE", "FIXED", "HTML", "3"),
            ("Bookkeeping cleanup project", "Accounting", "CONTRACT", "FIXED", "Bookkeeping", "3"),
        ]
        languages_by_city = {"Hyderabad": ["te", "hi"], "Bengaluru": ["kn", "en"], "Chennai": ["ta", "en"],
                             "Kochi": ["ml", "en"], "Coimbatore": ["ta"], "Kolkata": ["bn", "hi"],
                             "Visakhapatnam": ["te"], "Guwahati": ["as", "hi"], "Mumbai": ["mr", "hi"],
                             "Ahmedabad": ["gu", "hi"]}
        for city, count in counts.items():
            state, areas = cities[city]
            for index in range(count):
                title, category, job_type, salary_type, skill_name, level = offerings[(index + len(city)) % len(offerings)]
                area, latitude, longitude = areas[index % len(areas)]
                skill = skills[skill_name]
                task = self._task(
                    owner, f"{title} — {area}, {city}",
                    f"{title} for a local employer in {area}, {city}. Responsibilities include reliable, safe work, clear communication, and completing the agreed shift or deliverables. Relevant experience is welcome; the employer will confirm the schedule and tools before work begins.",
                    f"{(500 + ((index * 375 + len(city) * 11) % 14500)):.2f}",
                    f"{area}, {city}", [skill], work_mode=Task.WorkMode.ONSITE,
                    location_city=city, location_area=area, location_state=state,
                    location_address=f"{area}, {city}, {state}",
                    location_description=f"Local opportunity in {area}, {city}",
                    latitude=f"{latitude:.6f}", longitude=f"{longitude:.6f}",
                    job_type=getattr(Task.JobType, job_type), salary_type=getattr(Task.SalaryType, salary_type),
                    category=category, skill_level=f"LEVEL_{level}",
                    required_languages=languages_by_city.get(city, ["en"]),
                    experience_requirement={"1": "Entry level; training provided", "2": "Some relevant experience preferred", "3": "Experienced professional"}[level],
                    working_hours="Shift and schedule agreed with the employer",
                )
                task.location_city, task.location_area, task.location_state = city, area, state
                task.latitude, task.longitude = f"{latitude:.6f}", f"{longitude:.6f}"
                task.category, task.skill_level = category, f"LEVEL_{level}"
                task.required_languages = languages_by_city.get(city, ["en"])
                task.job_type, task.salary_type = getattr(Task.JobType, job_type), getattr(Task.SalaryType, salary_type)
                task.save(update_fields=["location_city", "location_area", "location_state", "latitude", "longitude", "category", "skill_level", "required_languages", "job_type", "salary_type", "updated_at"])

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
        Transaction.objects.get_or_create(assignment=completed_assignment, payer=users["second_client"], defaults={"amount": "9000.00", "currency": "INR", "provider": "RAZORPAY_TEST", "provider_order_id": f"demo_order_reporting_{completed_assignment.id}", "provider_payment_id": f"demo_payment_reporting_{completed_assignment.id}", "status": Transaction.Status.VERIFIED})

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
