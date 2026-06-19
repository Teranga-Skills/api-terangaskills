from django.db import models
import uuid

class Citoyen(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)

    date_naissance = models.DateField(null=True, blank=True)

    numero_identification = models.CharField(max_length=50, unique=True, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)