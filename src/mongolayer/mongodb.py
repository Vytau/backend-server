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
        get user by email
        """
        try:
            user = self.db['users'].find_one({'email': str(email)})
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

    def update_directory_meta(self, **kwargs):
        """
        Update file name of given file.
        """
        dir_id = kwargs['dir_id']
        folder_name = kwargs['folder_name']
        try:
            dir_ = self.db['directories'].update_one({
                '_id': ObjectId(dir_id)
            }, {
                '$set': {
                    'folder_name': folder_name
                }
            })
            if dir_:
                if self.update_content_meta(
                    content_id=dir_id,
                    name=folder_name
                ):
                    return True
            else:
                return False
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

    def update_content_meta(self, **kwargs):
        """
        Update content name.
        """
        content_id = kwargs['content_id']
        name = kwargs['name']
        try:
            file_ = self.db['content'].update_one({
                'content_id': content_id
            }, {
                '$set': {
                    'name': name
                }
            })
            if file_:
                print(file_)
                return file_
            else:
                return None
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

    def get_file_by_file_id(self, file_id):
        """
        Get a file by file id
        """
        try:
            file_ = self.db['files'].find_one({
                '_id': ObjectId(file_id)
            })
            if file_:
                return file_
            else:
                return None
        except:
            print(traceback.format_exc())
            raise

    def update_file_meta(self, **kwargs):
        """
        Update file name of given file.
        """
        file_id = kwargs['file_id']
        file_name = kwargs['file_name']
        try:
            file_ = self.db['files'].update_one({
                '_id': ObjectId(file_id)
            }, {
                '$set': {
                    'file_name': file_name
                }
            })
            if file_:
                if self.update_content_meta(
                    content_id=file_id,
                    name=file_name
                ):
                    return True
            else:
                return False
        except:
            print(traceback.format_exc())
            raise

    def update_file_data(self, **kwargs):
        """
        Update text of given file.
        """
        user_id = kwargs['user_id']
        file_id = kwargs['file_id']
        text = kwargs['text']
        try:
            file_ = self.db['files'].update_one({
                '_id': ObjectId(file_id)
            }, {
                '$set': {
                    'text': text
                }
            })
            if file_:
                print(file_)
                return file_
            else:
                return None
        except:
            print(traceback.format_exc())
            raise

    def delete_file_by_id(self, file_id):
        """
        Delete given file.
        """
        try:
            file_ = self.db['files'].update_one({
                '_id': ObjectId(file_id)
            }, {
                '$set': {
                    'deleted': True
                }
            })
            if file_:
                con = self.db['content'].remove({'content_id': file_id})
                return True
            else:
                return False
        except:
            print(traceback.format_exc())
            raise

    def generate_aut_token(self, **kwargs):
        """
        Generate auth token for given user.
        """
        user_id = kwargs['user_id']
        auth_token = kwargs['auth_token']
        refresh_token = kwargs['refresh_token']
        expire_time = datetime.datetime.now() + datetime.timedelta(minutes=10)

        try:
            token = self.db['auth'].save(db_models.CustomModel(
                user_id=user_id,
                auth_token=auth_token,
                refresh_token=refresh_token,
                expire_time=expire_time
            ))
            if token:
                return True
            return False
        except:
            print(traceback.format_exc())
            raise

    def validate_auth_token(self, **kwargs):
        """
        Validate given token.
        """
        user_id = kwargs['user_id']
        auth_token = kwargs['auth_token']
        refresh_token = kwargs['refresh_token']

        try:
            token = self.db['auth'].find_one({'user_id': str(user_id)} and
                                                    {'auth_token': str(auth_token)})
            if token:
                if datetime.datetime.now() < token['expire_time']:
                    return True
                else:
                    return self.refresh_auth_token(refresh_token, token)
            return False
        except:
            print(traceback.format_exc())
            raise

    def refresh_auth_token(self, recieved_token, token):
        if recieved_token == token['refresh_token']:
            res = self.db['auth'].update_one({
                '_id': ObjectId(token['_id'])
            }, {
                '$set': {
                    'expire_time': datetime.datetime.now() + datetime.timedelta(minutes=10)
                }
            })
            if res:
                return True
        return False

    def clone(self, **kwargs):
        if 'File' in kwargs['type']:
            res = self.copy_helper_file(kwargs['content_id'],  kwargs['toPaste'])
        else:
            self.copy_helper_dir(kwargs['content_id'], kwargs['toPaste'])
        return True

    def copy_helper_file(self, content_id, new_parent_id):
        file_ = self.get_file_by_file_id(content_id)
        file_['parent_dir_id'] = new_parent_id
        file_['user_id'] = file_['owner_id']
        return self.create_new_file(**file_)

    def copy_helper_dir(self, content_id, new_parent_id):
        temp_dir = self.get_directory_by_dir_id(content_id)
        temp_dir['parent_dir_id'] = new_parent_id
        temp_dir['user_id'] = temp_dir['owner_id']
        new_con =  self.create_new_directory(**temp_dir)
        sub_con = self.list_content_by_dir_id(
            dir_id=str(content_id),
            user_id=temp_dir['user_id']
        )
        if sub_con:
            for c in sub_con:
                if 'Directory' in c['type']:
                    self.copy_helper_dir(c['content_id'], new_con['content_id'])
                else:
                    self.copy_helper_file(c['content_id'],  new_con['content_id'])
