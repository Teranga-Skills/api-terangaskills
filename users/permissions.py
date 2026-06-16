from rest_framework import permissions

from .models import UserRole


class IsAdminUser(permissions.BasePermission):
    """
    Permission métier: compte ADMIN ou superuser.
    """

    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.role == UserRole.ADMIN)
        )


class IsAdminRole(IsAdminUser):
    """
    Alias explicite pour la lecture métier.
    """
    pass


class IsAgentRole(permissions.BasePermission):
    """
    Permission métier: compte AGENT.
    """

    message = "Accès réservé aux agents."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role == UserRole.AGENT
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Autorise si l’objet appartient à l’utilisateur courant
    ou si l’utilisateur courant est ADMIN/superuser.
    """

    message = "Accès refusé."

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (obj == user or user.is_superuser or user.role == UserRole.ADMIN)
        )