from django.db import models
import uuid

from signalements.models.centre import CentreEtatCivil


class RegistreEtatCivil(models.Model):
    """
    Registre officiel de référence pour la comparaison anti-fraude.
    Les entrées sont créées via l'admin ou l'API — aucune donnée en dur.
    """

    TYPE_ACTE = (
        ("NAISSANCE", "Naissance"),
        ("MARIAGE", "Mariage"),
        ("DECES", "Décès"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    numero_identification = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField(null=True, blank=True)
    type_acte = models.CharField(max_length=20, choices=TYPE_ACTE, default="NAISSANCE")
    numero_acte_officiel = models.CharField(max_length=100, null=True, blank=True)

    centre = models.ForeignKey(
        CentreEtatCivil,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registre_entries",
    )

    actif = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Registre état civil"
        verbose_name_plural = "Registre état civil"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.numero_identification})"
