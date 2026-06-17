from signalements.models import ActeEtatCivil


def find_best_match(extracted):

    numero = extracted.get("numero_identification")

    if not numero:
        return None

    try:
        return ActeEtatCivil.objects.get(
            citoyen__numero_identification=numero
        )
    except:
        return None