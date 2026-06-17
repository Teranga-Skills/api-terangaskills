from django.db import models
import uuid


class Region(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    nom = models.CharField(max_length=100, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom


class Commune(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    nom = models.CharField(max_length=100)

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="communes"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("nom", "region")

    def __str__(self):
        return f"{self.nom} ({self.region.nom})"


class CentreEtatCivil(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    code = models.CharField(max_length=64, unique=True)

    nom = models.CharField(max_length=255)

    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="centres"
    )

    commune = models.ForeignKey(
        Commune,
        on_delete=models.PROTECT,
        related_name="centres"
    )

    adresse = models.CharField(max_length=255, null=True, blank=True)

    telephone = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["region", "commune"]),
        ]

    def __str__(self):
        return f"{self.nom} ({self.code})"