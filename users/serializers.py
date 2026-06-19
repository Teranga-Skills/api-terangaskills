import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from .models import UserRole

_token_generator = PasswordResetTokenGenerator()

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    groups = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    user_permissions = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "is_active",
            "is_staff",
            "is_superuser",
            "created_by",
            "date_joined",
            "last_login",
            "groups",
            "user_permissions",
        ]
        read_only_fields = fields


class LoginSerializer(TokenObtainPairSerializer):
    """
    Login JWT personnalisé basé sur l’email.

    Retourne:
    - access
    - refresh
    - user: profil métier complet
    """

    username_field = "email"
    default_error_messages = {
        "no_active_account": _("Identifiants invalides"),
    }

    def validate(self, attrs):
        request = self.context.get("request")
        email = attrs.get(self.username_field)

        user = None
        if email:
            user = User.objects.filter(email__iexact=email).first()
            if user and not user.is_active:
                raise AuthenticationFailed("Compte désactivé", code="account_disabled")

        # TokenObtainPairSerializer gère l’authentification,
        # l’émission des tokens et la mise à jour last_login si activée.
        data = super().validate(attrs)

        data["user"] = UserDetailSerializer(self.user, context=self.context).data
        data["role"] = self.user.role
        data["first_name"] = self.user.first_name
        data["last_name"] = self.user.last_name

        # Optionnel, utile pour le debugging / audit côté client si besoin.
        if request is not None:
            data["login_source"] = "api"

        return data


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "role", "phone", "centre"]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "role": {"required": False},
            "centre": {"required": True},
            "phone": {"required": False, "allow_null": True, "allow_blank": True},
        }

    def validate_password(self, value):
        if value and len(value) < 8:
            raise serializers.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        if value:
            validate_password(value)
        return value

    def validate_role(self, value):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            if not request.user.is_superuser and value == UserRole.ADMIN:
                raise serializers.ValidationError("Seul un superuser peut créer un ADMIN.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not password:
            password = secrets.token_urlsafe(12)

        # created_by est injecté via serializer.save(created_by=request.user)
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["is_active", "role", "phone"]

    def validate_role(self, value):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            if not request.user.is_superuser and value == UserRole.ADMIN:
                raise serializers.ValidationError("Seul un superuser peut attribuer le rôle ADMIN.")
        return value

    def update(self, instance, validated_data):
        for attr in ["is_active", "role", "phone"]:
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = self.context["request"].user

        if attrs["new_password"] != attrs["confirm"]:
            raise serializers.ValidationError({"confirm": "La confirmation ne correspond pas."})

        if len(attrs["new_password"]) < 8:
            raise serializers.ValidationError({"new_password": "Le mot de passe doit contenir au moins 8 caractères."})

        validate_password(attrs["new_password"])
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"old_password": "Ancien mot de passe invalide."})

        if user.check_password(attrs["new_password"]):
            raise serializers.ValidationError({"new_password": "Le nouveau mot de passe doit être différent de l’ancien."})

        return attrs
    
class SetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user_pk = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_pk)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Lien invalide."})

        if not _token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Lien invalide ou expiré."})

        if attrs["new_password"] != attrs["confirm"]:
            raise serializers.ValidationError({"confirm": "La confirmation ne correspond pas."})

        validate_password(attrs["new_password"], user)
        attrs["user"] = user
        return attrs