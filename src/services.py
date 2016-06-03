from __future__ import absolute_import

import traceback
import bcrypt
import syringe


class KeyboardInterruptError(Exception):
    pass


@syringe.provides('mongodb-service')
class MongoDbService(object):
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
            return self.mongodb_handler.create_user(**kwargs)
        except:
            raise

    def is_user_exists(self, email):
        try:
            return self.mongodb_handler.is_user_exists(email)
        except:
            raise
