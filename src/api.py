# encoding: utf-8

from __future__ import absolute_import

import syringe
import bcrypt
import functools
import logging
from bson import ObjectId
import datetime
import json
import tornado.escape
import tornado.ioloop
import tornado.web
from tornado import gen
import traceback


def custom_encoder(self, obj):
    if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return str(obj)

json.JSONEncoder.default = custom_encoder


def authenticated_async(f):
    @functools.wraps(f)
    @tornado.web.asynchronous
    def wrapper(self, *args, **kwargs):
        self.current_user = self.get_current_user()
        if self.current_user:
            logging.info('User successfully authenticated')
            f(self, *args, **kwargs)
        else:
            raise tornado.web.HTTPError(401, 'User not authenticated, '
                                             'aborting')
    return wrapper


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin",
                        self.request.headers.get("X-Real-IP") or self.request.remote_ip)
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "accept")

    def get_login_url(self):
        return u"/login"

    def write_error(self, status_code, **kwargs):
        if 'message' not in kwargs:
            kwargs['message'] = 'Unknown Error: '
        self.write(kwargs['message'])

    # @authenticated_async
    def get(self):
        if not self.current_user:
            print('you are differnt user')
        else:
            print('current' + self.current_user)
        self.render("login.html")

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if user_json:
            return tornado.escape.json_decode(user_json)
        else:
            return None
