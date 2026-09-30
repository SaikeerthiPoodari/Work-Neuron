# WorkNeuron demo guide

## Seed safe local data

```powershell
cd backend
python manage.py migrate
python manage.py seed_demo
```

The command creates synthetic client, worker, admin, skills, verified and pending employers, Hyderabad/Bengaluru worker locations, remote/on-site/hybrid tasks, full-time/part-time/daily-wage/weekend/festival/internship/freelance/contract jobs, applications, assignments, review, Razorpay TEST transaction, notifications, job report, complaint, and fraud alert data. It is idempotent and uses no real personal information.

Demo accounts use `DemoPass123!` by default:

- `demo.worker@workneuron.local`
- `demo.client@workneuron.local`
- `demo.admin@workneuron.local`

## Suggested walkthrough

1. Log in as the worker and complete profile fields: education, interests, current location, preferred radius, work mode, and skills.
2. Open Smart Matches and inspect the score factors and explanation.
3. Open Nearby Jobs, allow location once, switch between List View and Map View, and change the radius.
4. Use voice search with `Naaku Hyderabad lo part-time job kavali` or an English equivalent. Review the extracted filters before searching.
5. Open a task, inspect employer verification status, and apply.
6. Use Report this Job with a suspicious-job reason; log in as admin and resolve or dismiss the report.
7. Log in as the client, review applications, select a worker, track progress, complete the assignment, and create a Razorpay TEST transaction.
8. Review employer earnings, completed jobs, transaction details, ratings, reputation, notifications, complaints, and payment history.
9. Log in as admin, review analytics, verification queue, fraud alerts, job reports, and complaints.

Browser geolocation, microphone permission, OpenStreetMap tile access, PostgreSQL, Razorpay, object storage, HTTPS, and WebSockets require the relevant local or deployment environment support. The demo does not claim government verification or live payment processing.
