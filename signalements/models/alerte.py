from django.db import models
import uuid
from .centre import CentreEtatCivil
from .citoyen import Citoyen    
from .acte import ActeEtatCivil

class Alerte(models.Model):

    TYPE = (
        ("FRAUDE", "Fraude"),
        ("DOUBLON", "Doublon"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    acte = models.ForeignKey(ActeEtatCivil, on_delete=models.CASCADE)

    type_alerte = models.CharField(max_length=20, choices=TYPE)

    message = models.TextField()

    niveau_severite = models.IntegerField(default=1)

    est_resolue = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)