import os
from pymongo import MongoClient


print("creating db")
MONGO_URI = os.getenv("MONGO_URI")

if MONGO_URI is None:
    raise ValueError("MONGO_URI not found in the environment")

MONGO_CLIENT = MongoClient(MONGO_URI)


# class DB:
#     _instance = None

#     def __init__(self) -> None:

#     def __new__(cls) -> "DB":
#         if cls._instance is None:
#             cls._instance = super(DB, cls).__new__(cls)
#             cls._instance.__init__()

#         return cls._instance

#     # @staticmethod
#     # def get_mongo_url() -> str:
#     #     db = DB()

#     #     return db.MONGO_URI

#     @staticmethod
#     def get_mongo_client():
#         db = DB()

#         return db.MONGO
