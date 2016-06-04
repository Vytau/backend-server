# import tornado
import base64
import json
import traceback
import uuid
import datetime
from bson.objectid import ObjectId
from io import StringIO
import syringe
from src.mongolayer import models as db_models

import pymongo


@syringe.provides('mongodb-handler')
class MongoDbHandler(object):
    def __init__(self, application):
        self.db = application.syncdb

    def create_user(self, **kwargs):
        """
        Creates a new user.

        """
        name = kwargs['name']
        email = kwargs['email']
        hashed_pass = kwargs['hashed_pass']

        try:
            user = self.db['users'].save(db_models.User(
                user_name=name,
                email=email,
                password_hash=hashed_pass,
                user_creation_date=datetime.datetime.now()
            ))
            # print(user)
            return True
        except:
            print(traceback.format_exc())
            raise

    def get_user_by_email(self, email):
        """
        Check if users already exists
        """
        try:
            user = self.db['users'].find_one({'email': email})
            if user:
                return user
            else:
                return None

        except:
            print(traceback.format_exc())
            raise
