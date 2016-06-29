from __future__ import absolute_import

import traceback
import bcrypt
import syringe
import base64
import os
import re


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

    def get_home_dir_by_user_id(self, user_id):
        try:
            return self.mongodb_handler.get_home_dir_by_user_id(user_id)
        except:
            raise

    def update_directory_meta(self, **kwargs):
        try:
            return self.mongodb_handler.update_directory_meta(**kwargs)
        except:
            raise

    def delete_directory_by_id(self, dir_id):
        try:
            return self.mongodb_handler.delete_directory_by_id(dir_id)
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

    def clone(self, **kwargs):
        try:
            return self.mongodb_handler.clone(**kwargs)
        except:
            raise

@syringe.provides('bin-service')
class BinService(object):
    """
    The service layer for :class:`MongoDbHandler.`
    """

    mongodb_handler = syringe.inject('mongodb-handler')

    def list_deleted_content(self, **kwargs):
        try:
            return self.mongodb_handler.list_deleted_content(**kwargs)
        except:
            raise

    def delete_content(self, con_id):
        try:
            return self.mongodb_handler.delete_content(con_id)
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

    def update_file_meta(self, **kwargs):
        try:
            return self.mongodb_handler.updatedelete_directory_by_id_file_meta(**kwargs)
        except:
            raise

    def update_file_data(self, **kwargs):
        try:
            return self.mongodb_handler.update_file_data(**kwargs)
        except:
            raise

    def delete_file_by_id(self, file_id):
        try:
            return self.mongodb_handler.delete_file_by_id(file_id)
        except:
            raise


@syringe.provides('auth-service')
class AuthService(object):
    """
    The service layer for :class:`MongoDbHandler.`
    """

    mongodb_handler = syringe.inject('mongodb-handler')

    def generate_aut_token(self, **kwargs):
        try:
            return self.mongodb_handler.generate_aut_token(**kwargs)
        except:
            raise

    def generate_oauth2_token(self):
        """
        Generate an oauth2 access or refresh token.

        The token returned matches the syntax specified in
        `rfc6749 secion 8.1
        <https://tools.ietf.org/html/rfc6749#section-8.1>`_.

        Warning: **Do not use the same token for multiple cases.**

        Returns:
            unicode: A random oauth2 token.

        """
        token = base64.urlsafe_b64encode(os.urandom(30)).decode().replace('==', '')
        assert re.match(r'[\d\w_\.-]+', token), (
            'Generated token "{!r}" does not match rfc6749').format(token)

        refresh_token = base64.urlsafe_b64encode(os.urandom(30)).decode().replace('==', '')
        assert re.match(r'[\d\w_\.-]+', refresh_token), (
            'Generated token "{!r}" does not match rfc6749').format(refresh_token)
        return {
            'auth_token': token,
            'refresh_token': refresh_token
        }


    def validate_auth_token(self, **kwargs):
        try:
            return self.mongodb_handler.validate_auth_token(**kwargs)
        except:
            raise

@syringe.provides('share-service')
class ShareService(object):
    """
    The service layer for :class:`MongoDbHandler.`
    """

    mongodb_handler = syringe.inject('mongodb-handler')

    def create_share_repo(self, **kwargs):
        try:
            return self.mongodb_handler.create_share_repo(**kwargs)
        except:
            raise

    def list_shared_content(self, **kwargs):
        try:
            return self.mongodb_handler.list_shared_content(**kwargs)
        except:
            raise
