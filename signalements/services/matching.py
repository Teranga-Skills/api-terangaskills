from signalements.services.identification_utils import find_registre_by_identification


def find_best_match(extracted):
    numero = extracted.get("numero_identification")
    return find_registre_by_identification(numero)
