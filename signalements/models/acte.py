from django.db import models
import uuid
from signalements.models import Citoyen, CentreEtatCivil

class ActeEtatCivil(models.Model):

    TYPE_ACTE = (
        ("NAISSANCE", "Naissance"),
        ("MARIAGE", "Mariage"),
        ("DECES", "Décès"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    numero_acte = models.CharField(max_length=100, unique=True)

    type_acte = models.CharField(max_length=20, choices=TYPE_ACTE)

    citoyen = models.ForeignKey(Citoyen, on_delete=models.CASCADE)

    centre = models.ForeignKey(CentreEtatCivil, on_delete=models.SET_NULL, null=True)

    date_creation = models.DateTimeField(auto_now_add=True)