from signalements.models import FileSynchronisation
from signalements.services.pipeline import run_pipeline


def traiter_file_synchronisation():

    elements = FileSynchronisation.objects.filter(statut="EN_ATTENTE")

    for element in elements:

        try:
            fichier = element.donnees.get("fichier")

            resultats = run_pipeline(fichier, element.utilisateur)

            element.statut = "SYNCHRONISE"
            element.save()

        except Exception as e:

            element.statut = "ECHEC"
            element.message_erreur = str(e)
            element.save()