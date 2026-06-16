from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import UserRole

User = get_user_model()


class AuthTestCase(APITestCase):
    def create_user(
        self,
        email="user@example.com",
        password="Password123!",
        role=UserRole.AGENT,
        is_active=True,
        is_superuser=False,
        is_staff=False,
        first_name="Test",
        last_name="User",
    ):
        if is_superuser:
            return User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

        return User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=is_active,
            is_staff=is_staff,
        )

    def login(self, email, password):
        return self.client.post(
            reverse("users:login"),
            {"email": email, "password": password},
            format="json",
        )

    def test_login_success(self):
        user = self.create_user()
        response = self.login(user.email, "Password123!")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["role"], UserRole.AGENT)

    def test_login_failure(self):
        user = self.create_user()
        response = self.login(user.email, "WrongPassword123!")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
        self.assertIn("Identifiants invalides", str(response.data["detail"]))

    def test_refresh_success(self):
        user = self.create_user()
        login_response = self.login(user.email, "Password123!")
        refresh = login_response.data["refresh"]

        response = self.client.post(
            reverse("users:refresh"),
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_logout_blacklist(self):
        user = self.create_user()
        login_response = self.login(user.email, "Password123!")
        refresh = login_response.data["refresh"]
        access = login_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_response = self.client.post(
            reverse("users:logout"),
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Le même refresh token ne doit plus être utilisable.
        retry_response = self.client.post(
            reverse("users:refresh"),
            {"refresh": refresh},
            format="json",
        )
        self.assertIn(retry_response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])

    def test_create_user_by_admin(self):
        admin = self.create_user(
            email="admin@example.com",
            password="AdminPass123!",
            role=UserRole.ADMIN,
            is_superuser=True,
            is_staff=True,
            first_name="Super",
            last_name="Admin",
        )
        login_response = self.login(admin.email, "AdminPass123!")
        access = login_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(
            reverse("users:users"),
            {
                "email": "agent1@example.com",
                "password": "AgentPass123!",
                "first_name": "Agent",
                "last_name": "One",
                "phone": "+221700000000",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], UserRole.AGENT)
        self.assertIn("temporary_password", response.data)

    def test_create_user_by_agent_forbidden(self):
        agent = self.create_user(
            email="agent@example.com",
            password="AgentPass123!",
            role=UserRole.AGENT,
            first_name="Field",
            last_name="Agent",
        )
        login_response = self.login(agent.email, "AgentPass123!")
        access = login_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(
            reverse("users:users"),
            {
                "email": "agent2@example.com",
                "password": "AgentPass123!",
                "first_name": "Agent",
                "last_name": "Two",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_without_token(self):
        response = self.client.get(reverse("users:me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)