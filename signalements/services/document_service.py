import hashlib


def generer_hash_document(file):

    for chunk in file.chunks():

        return hashlib.sha256(chunk).hexdigest()