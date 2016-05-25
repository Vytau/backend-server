from __future__ import absolute_import

import traceback

import syringe


class KeyboardInterruptError(Exception):
    pass


# @syringe.provides('mongodb-service')
class MongoDbService(object):
    """
    The service layer for :class:`MongoDbHandler.`
    """

    # def store_data_set(self, **kwargs):
    #     try:
    #         return self.mongodb_handler.store_data_set(**kwargs)
    #     except:
    #         raise
