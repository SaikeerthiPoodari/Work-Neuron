from django.core.exceptions import ValidationError
from django.db import transaction

from apps.assignments.models import Assignment
from apps.tasks.models import Task

from .models import Application


@transaction.atomic
def submit_application(application, worker):
    task = Task.objects.select_for_update().get(pk=application.task_id)
    if task.status not in (Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED):
        raise ValidationError("Applications are closed for this task.")
    application.worker = worker
    application.save()
    if task.status == Task.Status.OPEN:
        task.status = Task.Status.APPLICATIONS_RECEIVED
        task.save(update_fields=["status", "updated_at"])
    from apps.notifications.models import Notification
    from apps.notifications.services import create_notification
    create_notification(task.owner, Notification.Kind.APPLICATION_RECEIVED, "New application", f"{worker.email} applied to {task.title}.", f"/tasks/{task.id}")
    return application


@transaction.atomic
def decide_application(application, action):
    application = Application.objects.select_for_update().select_related("task").get(pk=application.pk)
    task = Task.objects.select_for_update().get(pk=application.task_id)
    if application.status != Application.Status.SUBMITTED:
        raise ValidationError("Only submitted applications can be decided.")
    if action == "reject":
        application.status = Application.Status.REJECTED
        application.save(update_fields=["status", "updated_at"])
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        create_notification(application.worker, Notification.Kind.APPLICATION_REJECTED, "Application rejected", f"Your application for {task.title} was rejected.", f"/tasks/{task.id}")
        return None
    if task.status != Task.Status.APPLICATIONS_RECEIVED:
        raise ValidationError("This task is no longer accepting an assignment.")
    assignment = Assignment.objects.create(task=task, worker=application.worker, application=application)
    application.status = Application.Status.ACCEPTED
    application.save(update_fields=["status", "updated_at"])
    Application.objects.filter(task=task, status=Application.Status.SUBMITTED).exclude(pk=application.pk).update(
        status=Application.Status.REJECTED
    )
    task.status = Task.Status.ASSIGNED
    task.save(update_fields=["status", "updated_at"])
    from apps.notifications.models import Notification
    from apps.notifications.services import create_notification
    create_notification(application.worker, Notification.Kind.APPLICATION_ACCEPTED, "Application accepted", f"You were selected for {task.title}.", f"/assignments/{assignment.id}")
    return assignment


@transaction.atomic
def withdraw_application(application, worker):
    if application.worker_id != worker.id:
        raise ValidationError("You can withdraw only your own application.")
    if application.status != Application.Status.SUBMITTED:
        raise ValidationError("Only submitted applications can be withdrawn.")
    application.status = Application.Status.WITHDRAWN
    application.save(update_fields=["status", "updated_at"])
    task = Task.objects.select_for_update().get(pk=application.task_id)
    if task.status == Task.Status.APPLICATIONS_RECEIVED and not task.applications.filter(status=Application.Status.SUBMITTED).exists():
        task.status = Task.Status.OPEN
        task.save(update_fields=["status", "updated_at"])
    from apps.notifications.models import Notification
    from apps.notifications.services import create_notification
    create_notification(task.owner, Notification.Kind.APPLICATION_WITHDRAWN, "Application withdrawn", f"{worker.email} withdrew an application for {task.title}.", f"/tasks/{task.id}")
