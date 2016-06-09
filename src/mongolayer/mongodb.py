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
            dir_ = self.create_new_directory(
                user_id=str(user),
                folder_name="Home",
                parent_dir_id=str(user),
                contributors=[]
            )
            # set up home directory for newley created user.
            self.create_home_directory(str(user), str(dir_['_id']))
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
                deleted=False,
                dir_creation_date=datetime.datetime.now()
            ))
            # save newley created directory in to content repo.
            con = self.save_data_to_content_repo(
                user_id=user_id,
                name=folder_name,
                parent_id=parent_dir_id,
                content_id=str(dir_),
                type='Directory'
            )
            return self.get_content_by_content_id(str(con))
        except:
            print(traceback.format_exc())
            raise


    def create_home_directory(self, user_id, dir_id):
        """
        Create home directory for every new user.
        """
        try:
            dir_ = self.db['homedirectories'].save(db_models.CustomModel(
                user_id=user_id,
                dir_id=dir_id,
                dir_creation_date=datetime.datetime.now()
            ))
            return True
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

    def get_home_dir_by_user_id(self, u_id):
        """
        Get home directory by user id.
        """
        try:
            dir_ = self.db['homedirectories'].find_one({'user_id': str(u_id)})
            if dir_:
                return dir_
            else:
                return None
        except:
            print(traceback.format_exc())
            raise

    def save_data_to_content_repo(self, **kwargs):
        """
        Create content repo to store reference of files and folder,
        in order to reduce the datastore query load we will save the
        reference of the content.
        """
        try:
            dir_ = self.db['content'].save(db_models.CustomModel(
                user_id=kwargs['user_id'],
                parent_id=kwargs['parent_id'],
                content_id=kwargs['content_id'],
                name=kwargs['name'],
                type=kwargs['type'],
                dir_creation_date=datetime.datetime.now()
            ))
            return dir_
        except:
            print(traceback.format_exc())
            raise

    def list_content_by_dir_id(self, **kwargs):
        """
        List content of given directory.
        """
        dir_id = kwargs['dir_id']
        user_id = kwargs['user_id']
        try:
            content = self.db['content'].find({'user_id': str(user_id)} and
                                                {'parent_id': str(dir_id)})
            if content:
                return content
            else:
                return None

        except:
            print(traceback.format_exc())
            raise

    def get_content_by_content_id(self, content_id):
        """
        List content of given directory.
        """
        try:
            content = self.db['content'].find_one({
                '_id': ObjectId(content_id)
            })
            if content:
                return content
            else:
                return None

        except:
            print(traceback.format_exc())
            raise

    def create_new_file(self, **kwargs):
        """
        Creates new file.
        """
        file_name = kwargs['file_name']
        user_id = kwargs['user_id']
        text = kwargs['text']
        parent_dir_id = kwargs['parent_dir_id']
        contributors = kwargs['contributors'] # list of user

        try:
            file_ = self.db['files'].save(db_models.CustomModel(
                file_name=file_name,
                owner_id=user_id,
                contributors=contributors,
                parent_dir_id=parent_dir_id,
                deleted=False,
                text=text,
                dir_creation_date=datetime.datetime.now()
            ))
            # save newley created file in to content repo.
            con = self.save_data_to_content_repo(
                user_id=user_id,
                name=file_name,
                parent_id=parent_dir_id,
                content_id=str(file_),
                type='File'
            )
            return self.get_content_by_content_id(str(con))
        except:
            print(traceback.format_exc())
            raise
