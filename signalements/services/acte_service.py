import uuid
from datetime import datetime


def generer_numero_acte(type_acte: str, centre_code: str):

    year = datetime.now().year

    unique_part = str(uuid.uuid4())[:6].upper()

    return f"{type_acte[:3]}-{centre_code}-{year}-{unique_part}"