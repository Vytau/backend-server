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
            user = self.db['users'].save(db_models.CustomModel(
                user_name=name,
                email=email,
                password_hash=hashed_pass,
                user_creation_date=datetime.datetime.now()
            ))
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

    def create_new_directory(self, **kwargs):
        """
        Creates new directory.
        """
        folder_name = kwargs['folder_name']
        user_id = kwargs['user_id']
        parent_dir_id = kwargs['parent_dir_id']
        contributors = kwargs['contributors'] # list of user

        try:
            dir_ = self.db['directories'].save(db_models.CustomModel(
                folder_name=folder_name,
                owner_id=user_id,
                contributors=contributors,
                parent_dir_id=parent_dir_id,
                dir_creation_date=datetime.datetime.now()
            ))
            return self.get_directory_by_dir_id(dir_)
        except:
            print(traceback.format_exc())
            raise

    def get_directory_by_dir_id(self, dir_id):
        """
        Get directory by dir id
        """
        try:
            dir_ = self.db['directories'].find_one({
                '_id': ObjectId(dir_id)
            })
            if dir_:
                return dir_
            else:
                return None
        except:
            print(traceback.format_exc())
            raise
