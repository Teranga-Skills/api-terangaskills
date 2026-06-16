from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crée un superuser de bootstrap à partir des variables d'environnement."

    def handle(self, *args, **options):
        User = get_user_model()

        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        first_name = os.environ.get("DJANGO_SUPERUSER_FIRST_NAME", "Super")
        last_name = os.environ.get("DJANGO_SUPERUSER_LAST_NAME", "Admin")

        if not email or not password:
            raise CommandError(
                "Les variables DJANGO_SUPERUSER_EMAIL et DJANGO_SUPERUSER_PASSWORD sont obligatoires."
            )

        existing = User.objects.filter(email__iexact=email).first()
        if existing:
            self.stdout.write(self.style.SUCCESS(f"Superuser déjà existant: {email}"))
            return

        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        self.stdout.write(self.style.SUCCESS(f"Superuser créé avec succès: {user.email}"))