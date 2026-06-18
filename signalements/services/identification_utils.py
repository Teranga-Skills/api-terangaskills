"""
Normalisation et comparaison souple des numéros d'identification.

Les identifiants n'ont pas de format imposé (pas obligatoirement préfixés par « SN »).
La comparaison ignore espaces, tirets, points, casse, et certains préfixes courants.
"""

from __future__ import annotations

import re
from typing import Optional, Set

from signalements.models import ActeEtatCivil

_PREFIXES_OPTIONNELS = ("SNP", "SN", "SEN", "ID", "NIN")


def sanitize_identification(value: Optional[str]) -> str:
    """Retire les préfixes alphabétiques ; le numéro doit commencer par un chiffre."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.upper() == "UNKNOWN":
        return ""

    i = 0
    while i < len(text) and not text[i].isdigit():
        i += 1
    return text[i:].strip() if i < len(text) else ""


def identification_starts_with_digit(value: Optional[str]) -> bool:
    sanitized = sanitize_identification(value)
    return bool(sanitized) and sanitized[0].isdigit()


def normalize_identification(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = str(value).strip().upper()
    if not text or text == "UNKNOWN":
        return ""
    return re.sub(r"[^A-Z0-9]", "", text)


def identification_keys(value: Optional[str]) -> Set[str]:
    """Clés comparables pour un même numéro sous différents formats."""
    base = normalize_identification(value)
    if not base:
        return set()

    keys: Set[str] = {base}

    for prefix in _PREFIXES_OPTIONNELS:
        if base.startswith(prefix) and len(base) > len(prefix) + 3:
            keys.add(base[len(prefix):])

    return keys


def identifications_match(a: Optional[str], b: Optional[str]) -> bool:
    keys_a = identification_keys(a)
    keys_b = identification_keys(b)
    if not keys_a or not keys_b:
        return False

    if keys_a & keys_b:
        return True

    for ka in keys_a:
        for kb in keys_b:
            shorter, longer = (ka, kb) if len(ka) <= len(kb) else (kb, ka)
            if len(shorter) >= 6 and longer.endswith(shorter):
                return True

    return False


def find_acte_by_identification(numero: Optional[str]) -> Optional[ActeEtatCivil]:
    """Recherche un acte via le numéro d'identification du citoyen (comparaison souple)."""
    target_keys = identification_keys(numero)
    if not target_keys:
        return None

    numero_normalise = normalize_identification(numero)
    correspondance_exacte: list[ActeEtatCivil] = []
    correspondance_souple: list[ActeEtatCivil] = []

    queryset = ActeEtatCivil.objects.select_related("citoyen", "centre").all()

    for acte in queryset:
        citoyen_num = acte.citoyen.numero_identification
        if not citoyen_num:
            continue

        if normalize_identification(citoyen_num) == numero_normalise:
            correspondance_exacte.append(acte)
        elif identifications_match(numero, citoyen_num):
            correspondance_souple.append(acte)

    if correspondance_exacte:
        return correspondance_exacte[0]
    if correspondance_souple:
        return correspondance_souple[0]
    return None
