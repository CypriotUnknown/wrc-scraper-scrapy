import os
from pymongo import MongoClient


print("creating db")
MONGO_URI = os.getenv("MONGO_URI")

if MONGO_URI is None:
    raise ValueError("MONGO_URI not found in the environment")

MONGO_CLIENT = MongoClient(MONGO_URI)
