import json
import secrets

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import OutstandingToken, RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import AuditAction, AuditLog, UserRole
from .permissions import IsAdminUser
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


def get_client_ip(request) -> str | None:
    """
    Récupération simple et robuste de l’IP.
    En production derrière proxy, `X-Forwarded-For` doit être nettoyé côté infra.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def safe_details(payload) -> dict:
    """
    Garantit un JSON simple et sérialisable pour AuditLog.details.
    """
    try:
        json.dumps(payload)
        return payload
    except Exception:
        return {"raw": str(payload)}


def blacklist_all_user_refresh_tokens(user: User) -> int:
    """
    Blacklist tous les refresh tokens outstanding d’un utilisateur.

    Important:
    - SimpleJWT conserve les refresh tokens en base via le blacklist app.
    - Cela invalide les refresh tokens existants.
    - Les access tokens déjà émis restent valides jusqu’à expiration.
    """
    blacklisted = 0
    tokens = OutstandingToken.objects.filter(user=user)

    for outstanding in tokens:
        try:
            RefreshToken(outstanding.token).blacklist()
            blacklisted += 1
        except TokenError:
            # Token déjà expiré ou token impossible à blacklister.
            continue
        except Exception:
            continue

    return blacklisted


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class LoginView(APIView):
    """
    POST /api/v1/auth/login/

    Corps:
    {
        "email": "...",
        "password": "..."
    }

    Réponse:
    {
        "access": "...",
        "refresh": "...",
        "user": {...}
    }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        ip_address = get_client_ip(request)
        serializer = LoginSerializer(data=request.data, context={"request": request})

        try:
            serializer.is_valid(raise_exception=True)
        except (ValidationError, AuthenticationFailed) as exc:
            email = request.data.get("email")
            user = User.objects.filter(email__iexact=email).first() if email else None
            AuditLog.objects.create(
                user=user,
                action=AuditAction.LOGIN_FAILED,
                ip_address=ip_address,
                success=False,
                details=safe_details(
                    {
                        "email": email,
                        "error": getattr(exc, "detail", str(exc)),
                        "timestamp": timezone.now().isoformat(),
                    }
                ),
            )
            raise

        user = serializer.user

        AuditLog.objects.create(
            user=user,
            action=AuditAction.LOGIN,
            ip_address=ip_address,
            success=True,
            details=safe_details(
                {
                    "email": user.email,
                    "role": user.role,
                    "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                    "timestamp": timezone.now().isoformat(),
                }
            ),
        )

        response_payload = serializer.validated_data

        # Nettoyage explicitement contrôlé.
        return Response(
            {
                "access": response_payload.get("access"),
                "refresh": response_payload.get("refresh"),
                "user": response_payload.get("user"),
                "role": response_payload.get("role"),
                "first_name": response_payload.get("first_name"),
                "last_name": response_payload.get("last_name"),
            },
            status=status.HTTP_200_OK,
        )


class CustomTokenRefreshView(TokenRefreshView):
    """
    POST /api/v1/auth/refresh/

    Délègue à SimpleJWT TokenRefreshView.
    La route est gardée explicite pour l’API du projet.
    """

    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/

    Corps:
    {
        "refresh": "..."
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ip_address = get_client_ip(request)
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.LOGOUT,
                ip_address=ip_address,
                success=False,
                details={"error": "refresh token manquant"},
            )
            raise ValidationError({"refresh": "Le refresh token est obligatoire."})

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.LOGOUT,
                ip_address=ip_address,
                success=False,
                details={"error": "refresh token invalide ou déjà révoqué"},
            )
            raise ValidationError({"refresh": "Refresh token invalide ou déjà révoqué."})

        AuditLog.objects.create(
            user=request.user,
            action=AuditAction.LOGOUT,
            ip_address=ip_address,
            success=True,
            details={
                "timestamp": timezone.now().isoformat(),
                "logout_mode": "blacklist_refresh_token",
            },
        )

        return Response(
            {"detail": "Déconnexion effectuée avec succès."},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """
    GET /api/v1/auth/me/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserListCreateView(APIView):
    """
    GET /api/v1/users/
    POST /api/v1/users/

    Réservé aux administrateurs.
    """

    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination

    def get_queryset(self):
        return User.objects.select_related("created_by").all().order_by("-date_joined")

    def get(self, request):
        queryset = self.get_queryset()

        role = request.query_params.get("role")
        if role:
            queryset = queryset.filter(role=role)

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            normalized = str(is_active).strip().lower()
            if normalized in {"true", "1", "yes", "y"}:
                queryset = queryset.filter(is_active=True)
            elif normalized in {"false", "0", "no", "n"}:
                queryset = queryset.filter(is_active=False)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = UserDetailSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        # Ce endpoint crée un AGENT par design.
        # Le rôle ADMIN reste possible via l’admin Django ou un superuser si besoin,
        # mais on force ici le cas d’usage métier.
        payload = request.data.copy()
        payload["role"] = UserRole.AGENT

        initial_password = payload.get("password")
        if not initial_password:
            initial_password = secrets.token_urlsafe(12)
            payload["password"] = initial_password

        serializer = UserCreateSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save(created_by=request.user)
            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.CREATE_USER,
                ip_address=get_client_ip(request),
                success=True,
                details=safe_details(
                    {
                        "target_user_id": user.id,
                        "target_email": user.email,
                        "target_role": user.role,
                        "created_by_id": request.user.id,
                    }
                ),
            )

        output = UserDetailSerializer(user, context={"request": request}).data
        output["temporary_password"] = initial_password

        return Response(output, status=status.HTTP_201_CREATED)


class UserDetailUpdateView(APIView):
    """
    PATCH /api/v1/users/{id}/

    Réservé aux administrateurs.
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self, pk: int) -> User:
        try:
            return User.objects.select_related("created_by").get(pk=pk)
        except User.DoesNotExist as exc:
            raise ValidationError({"detail": "Utilisateur introuvable."}) from exc

    def patch(self, request, pk: int):
        user_obj = self.get_object(pk)
        serializer = UserUpdateSerializer(
            user_obj,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            updated = serializer.save()
            AuditLog.objects.create(
                user=request.user,
                action=AuditAction.UPDATE_USER,
                ip_address=get_client_ip(request),
                success=True,
                details=safe_details(
                    {
                        "target_user_id": updated.id,
                        "target_email": updated.email,
                        "updated_fields": list(serializer.validated_data.keys()),
                    }
                ),
            )

        return Response(UserDetailSerializer(updated, context={"request": request}).data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/

    Corps:
    {
        "old_password": "...",
        "new_password": "...",
        "confirm": "..."
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        blacklisted_count = blacklist_all_user_refresh_tokens(user)

        AuditLog.objects.create(
            user=user,
            action=AuditAction.CHANGE_PASSWORD,
            ip_address=get_client_ip(request),
            success=True,
            details=safe_details(
                {
                    "blacklisted_refresh_tokens": blacklisted_count,
                    "timestamp": timezone.now().isoformat(),
                }
            ),
        )

        return Response(
            {"detail": "Mot de passe modifié avec succès. Les refresh tokens ont été révoqués."},
            status=status.HTTP_200_OK,
        )