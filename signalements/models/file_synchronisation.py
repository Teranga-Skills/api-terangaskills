import uuid
from django.db import models
from django.conf import settings



class FileSynchronisation(models.Model):

    STATUT = (
        ("EN_ATTENTE", "En attente"),
        ("SYNCHRONISE", "Synchronisé"),
        ("ECHEC", "Échec"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="files_synchronisation"
    )

    donnees = models.JSONField()

    statut = models.CharField(
        max_length=20,
        choices=STATUT,
        default="EN_ATTENTE"
    )

    message_erreur = models.TextField(null=True, blank=True)

    cree_le = models.DateTimeField(auto_now_add=True)

    synchronise_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["statut"]),
            models.Index(fields=["cree_le"]),
        ]

    def __str__(self):
        return f"{self.utilisateur} - {self.statut}"