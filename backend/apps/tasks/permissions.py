from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsClientRole(BasePermission):
    message = "Only clients can create tasks."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.CLIENT)


class IsTaskOwnerOrAdmin(BasePermission):
    message = "Only the task owner or an administrator can modify this task."

    def has_object_permission(self, request, view, obj):
        return bool(request.user.role == User.Role.ADMIN or obj.owner_id == request.user.id)

