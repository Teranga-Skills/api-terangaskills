from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    AGENT = "AGENT", "Agent"


class AuditAction(models.TextChoices):
    LOGIN = "LOGIN", "Login"
    LOGIN_FAILED = "LOGIN_FAILED", "Login Failed"
    LOGOUT = "LOGOUT", "Logout"
    CREATE_USER = "CREATE_USER", "Create User"
    UPDATE_USER = "UPDATE_USER", "Update User"
    CHANGE_PASSWORD = "CHANGE_PASSWORD", "Change Password"
    TOKEN_REFRESH = "TOKEN_REFRESH", "Token Refresh"


class CustomUserManager(BaseUserManager):
    """
    Manager sans username, basé sur email.

    Règle importante:
    - create_user() ne génère jamais de mot de passe aléatoire.
    - le mot de passe doit être fourni explicitement.
    """

    use_in_migrations = True

    def normalize_email_value(self, email: str) -> str:
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        return self.normalize_email(email).strip().lower()

    def create_user(self, email: str, password: str, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        if not password:
            raise ValueError("Le mot de passe doit être fourni explicitement.")

        email = self.normalize_email_value(email)
        extra_fields.setdefault("role", UserRole.AGENT)
        extra_fields.setdefault("is_active", True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=None)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        if not password:
            raise ValueError("Le mot de passe du superutilisateur doit être fourni.")
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superuser doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superuser doit avoir is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True, null=True)

    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.AGENT,
        db_index=True,
    )

    # Champ critique pour le contrôle d’accès à l’admin Django.
    # is_staff n’est pas un "rôle métier" ; c’est un flag technique.
    is_staff = models.BooleanField(default=False)

    # Seul l’admin peut activer/désactiver un compte.
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
    )

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
        ]

    def save(self, *args, **kwargs):
        # Normalisation défensive, y compris lors d’un save manuel hors manager.
        if self.email:
            self.email = self.email.strip().lower()

        # Cohérence sécurité/métier :
        # - un ADMIN métier doit pouvoir accéder au dashboard Django
        # - un AGENT ne doit pas obtenir l’accès admin par erreur
        # - un superuser garde toujours is_staff=True
        if self.is_superuser:
            self.is_staff = True
        elif self.role == UserRole.ADMIN:
            self.is_staff = True
        else:
            self.is_staff = False

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        full_name = f"{self.first_name} {self.last_name}".strip()
        label = full_name if full_name else self.email
        return f"{label} — {self.email} [{self.get_role_display()}]"

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        return self.first_name or self.email


class AuditLog(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=40, choices=AuditAction.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Journal d’audit"
        verbose_name_plural = "Journaux d’audit"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["success"]),
        ]

    def __str__(self) -> str:
        user_label = self.user.email if self.user else "système"
        return f"{self.action} — {user_label} — {self.timestamp:%Y-%m-%d %H:%M:%S}"


@receiver(post_save, sender=CustomUser)
def log_user_creation(sender, instance: CustomUser, created: bool, **kwargs):
    """
    Auto-log uniquement pour la création initiale sans created_by.
    Cela couvre notamment le bootstrap initial via createsuperuser/seed_admin
    sans dupliquer les logs métier de l’endpoint /api/v1/users/.
    """
    if created and instance.created_by is None:
        AuditLog.objects.create(
            user=instance,
            action=AuditAction.CREATE_USER,
            ip_address=None,
            success=True,
            details={
                "auto_logged": True,
                "bootstrap": True,
                "email": instance.email,
                "role": instance.role,
            },
        )