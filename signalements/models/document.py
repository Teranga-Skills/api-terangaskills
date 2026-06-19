from django.db import models
import uuid
from signalements.models import ActeEtatCivil


class Document(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    acte = models.OneToOneField(ActeEtatCivil, on_delete=models.CASCADE)

    fichier = models.FileField(upload_to="documents/")

    hash_document = models.CharField(max_length=255, unique=True)

    qualite_scan = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)