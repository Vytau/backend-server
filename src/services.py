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
            return self.mongodb_handler.get_user_by_email(email)
        except:
            raise
