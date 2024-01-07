"""
Conexión con Mongo.
"""

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import database as mdb


def get_db() -> mdb:
<<<<<<< HEAD
    uri = "mongodb+srv://adiazv:rLpbgvPkiAcvqhrN@r07.7dkjtpy.mongodb.net/?retryWrites=true&w=majority"
=======
    # Keyring must be installed in the python environment
    user = "adiazv"
    pwd = keyring.get_password("mongo-diego", user)
    uri = f"mongodb+srv://{user}:{pwd}@r07.7dkjtpy.mongodb.net/?retryWrites=true&w=majority"
>>>>>>> 687f86a (fixup! Resuelve tarjeta https://trello.com/c/ysdbSVt6)
    # Set the Stable API version when creating a new client
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    client.admin.command('ping')

    return client.r07_db
