"""
Conexión con Mongo.
"""

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import database as mdb
import keyring


def get_db() -> mdb:
    user = "adiazv"
    pwd = keyring.get_password("mongo-diego", user)
    uri = f"mongodb+srv://{user}:{pwd}@r07.7dkjtpy.mongodb.net/?retryWrites=true&w=majority"
    # Set the Stable API version when creating a new client
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    client.admin.command('ping')

    return client.r07_db
