import hashlib
import json

def dict_hash(dictionary):
    dhash = hashlib.md5()

    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()
