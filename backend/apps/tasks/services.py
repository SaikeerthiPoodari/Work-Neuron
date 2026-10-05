from django.core.exceptions import ValidationError

from .models import Task


ALLOWED_TRANSITIONS = {
    Task.Status.OPEN: {Task.Status.APPLICATIONS_RECEIVED, Task.Status.CANCELLED},
    Task.Status.APPLICATIONS_RECEIVED: {Task.Status.ASSIGNED, Task.Status.CANCELLED},
    Task.Status.ASSIGNED: {Task.Status.IN_PROGRESS, Task.Status.CANCELLED},
    Task.Status.IN_PROGRESS: {Task.Status.SUBMITTED, Task.Status.CANCELLED},
    Task.Status.SUBMITTED: {Task.Status.COMPLETED, Task.Status.CANCELLED},
    Task.Status.COMPLETED: set(),
    Task.Status.CANCELLED: set(),
}


def transition_task(task, new_status):
    if new_status == task.status:
        raise ValidationError("Task is already in this state.")
    if new_status not in ALLOWED_TRANSITIONS[task.status]:
        raise ValidationError(f"Invalid task transition from {task.status} to {new_status}.")
    task.status = new_status
    task.save(update_fields=["status", "updated_at"])
    return task

