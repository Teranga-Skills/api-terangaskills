from django.conf import settings
from django.db import models
import uuid

from signalements.models.citoyen import Citoyen
from signalements.models.centre import CentreEtatCivil


class ActeEtatCivil(models.Model):

    TYPE_ACTE = (
        ("NAISSANCE", "Naissance"),
        ("MARIAGE", "Mariage"),
        ("DECES", "Décès"),
    )

    STATUT = (
        ("EN_ATTENTE", "En attente"),
        ("VALIDE", "Validé"),
        ("SUSPECT", "Suspect fraude"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    numero_acte = models.CharField(max_length=100, unique=True, editable=False)

    type_acte = models.CharField(max_length=20, choices=TYPE_ACTE)

    statut = models.CharField(max_length=20, choices=STATUT, default="EN_ATTENTE")

    citoyen = models.ForeignKey(Citoyen, on_delete=models.CASCADE, related_name="actes")

    centre = models.ForeignKey(CentreEtatCivil, on_delete=models.SET_NULL, null=True, related_name="actes")



    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actes_crees"
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.numero_acte