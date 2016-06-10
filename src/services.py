from __future__ import absolute_import

import traceback
import bcrypt
import syringe


class KeyboardInterruptError(Exception):
    pass


@syringe.provides('user-service')
class UserService(object):
    """
    The service layer for :class:`MongoDbHandler.`
    """
    mongodb_handler = syringe.inject('mongodb-handler')

    def create_user(self, **kwargs):
        try:
            # Warning bcrypt will block IO loop:
            hashed_pass = bcrypt.hashpw(kwargs['password'], bcrypt.gensalt(8))
            del kwargs['password']
            kwargs['hashed_pass'] = hashed_pass
            if self.mongodb_handler.create_user(**kwargs):
                return self.get_user_by_email(kwargs['email'])
            return False
        except:
            raise

    def get_user_by_email(self, email):
        try:
            user = self.mongodb_handler.get_user_by_email(email)
            # print(user)
            if user:
                home_dir = self.mongodb_handler.get_home_dir_by_user_id(user['_id'])
                if home_dir:
                    user['home_dir_id'] = home_dir['dir_id']
                return user
        except:
            raise


@syringe.provides('directory-service')
class DirectoryService(object):
    """
    The service layer for :class:`MongoDbHandler.`
    """
    mongodb_handler = syringe.inject('mongodb-handler')

    def create_new_directory(self, **kwargs):
        try:
            return self.mongodb_handler.create_new_directory(**kwargs)
        except:
            raise

    def get_home_dir_by_user_id(self, **kwargs):
        try:
            return self.mongodb_handler.get_home_dir_by_user_id(user_id)
        except:
            raise


@syringe.provides('content-service')
class ContentService(object):
    """
    The service layer for :class:`MongoDbHandler.`
    """

    mongodb_handler = syringe.inject('mongodb-handler')

    def list_content_by_dir_id(self, **kwargs):
        try:
            return self.mongodb_handler.list_content_by_dir_id(**kwargs)
        except:
            raise

@syringe.provides('file-service')
class FileService(object):
    """
    The service layer for :class:`MongoDbHandler.`
    """

    mongodb_handler = syringe.inject('mongodb-handler')

    def create_new_file(self, **kwargs):
        try:
            return self.mongodb_handler.create_new_file(**kwargs)
        except:
            raise

    def get_file_by_file_id(self, file_id):
        try:
            return self.mongodb_handler.get_file_by_file_id(file_id)
        except:
            raise
