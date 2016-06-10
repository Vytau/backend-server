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
        # self.set_header("Access-Control-Allow-Origin", self.request.headers['Origin']
        #                 self.request.headers.get("X-Real-IP") or self.request.remote_ip)
        self.set_header("Access-Control-Allow-Origin",
                            self.request.headers['Origin'])
        # self.set_header("Access-Control-Allow-Origin",
        #                     "http://145.93.177.18:8901/")
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "X-Requested-With,Content-Type,Accept,Origin")

    def get_login_url(self):
        return u"/login"

    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", tornado.escape.json_encode(user), 10)
        else:
            self.clear_cookie("user")

    def write_error(self, status_code, **kwargs):
        if 'message' not in kwargs:
            kwargs['message'] = 'Unknown Error: '
        self.write(kwargs['message'])

    # @authenticated_async
    def get(self):
        if not self.current_user:
            self.render("login.html")

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if user_json:
            return tornado.escape.json_decode(user_json)
        else:
            return None


class RegisterHandler(BaseHandler):
    user_service = syringe.inject('user-service')

    def post(self):
        self.set_header('Content-Type', 'application/json')
        email = self.get_argument('email', '')
        name = self.get_argument('name', '')
        if self.user_service.get_user_by_email(email):
            raise tornado.web.HTTPError(409, 'User already exists, '
                                             'aborting')
        password = self.get_argument('password', '').encode('utf-8')
        user = self.user_service.create_user(
            name=name,
            email=email,
            password=password,
            db=self.application.syncdb
        )
        if user:
            self.set_current_user(email)
            del user['password_hash']
            self.write(json.dumps(user))
        else:
            raise tornado.web.HTTPError(400, 'Registration Failed, '
                                             'aborting')
        self.finish()


class LoginHandler(BaseHandler):
    user_service = syringe.inject('user-service')

    @gen.coroutine
    def post(self):
        self.set_header('Content-Type', 'application/json')
        email = self.get_argument('email', '')
        password = self.get_argument('password', '').encode('utf-8')
        user = self.user_service.get_user_by_email(email)

        # Warning bcrypt will block IO loop:
        if user and user['password_hash'] and bcrypt.hashpw(password, user['password_hash']) == user['password_hash']:
            self.set_current_user(email)
            del user['password_hash']
            self.write(json.dumps(user))
        else:
            self.set_secure_cookie('flash', "Login incorrect")
            raise tornado.web.HTTPError(400, 'Loign Failed, '
                                             'aborting')


class LogoutHandler(BaseHandler):
    def post(self):
        self.clear_cookie("user")
        self.finish()


class DirectoryHandler(BaseHandler):
    dir_service = syringe.inject('directory-service')

    def post(self, user_id):
        self.set_header('Content-Type', 'application/json')

        data = tornado.escape.json_decode(self.request.body)
        dir_ = self.dir_service.create_new_directory(
            user_id=user_id,
            folder_name=data['folder_name'],
            parent_dir_id=data['parent_dir_id'],
            contributors=data['contributors']
        )
        if dir_:
            self.write(json.dumps(dir_))
        else:
            self.send_error(
                400,
                message='Directory Creation failed.'
            )
        self.finish()


class ContentHandler(BaseHandler):
    con_service = syringe.inject('content-service')

    def get(self, user_id, dir_id):
        self.set_header('Content-Type', 'application/json')
        content = self.con_service.list_content_by_dir_id(
            user_id=user_id,
            dir_id=dir_id
        )
        self.write(json.dumps([c for c in content]))
        self.finish()

class FileHandler(BaseHandler):
    file_service = syringe.inject('file-service')

    def post(self, user_id):
        self.set_header('Content-Type', 'application/json')

        data = tornado.escape.json_decode(self.request.body)
        dir_ = self.file_service.create_new_file(
            user_id=user_id,
            file_name=data['file_name'],
            text=data['text'],
            parent_dir_id=data['parent_dir_id'],
            contributors=data['contributors']
        )
        if dir_:
            self.write(json.dumps(dir_))
        else:
            self.send_error(
                400,
                message='File Creation failed.'
            )
        self.finish()

    def get(self, file_id):
        self.set_header('Content-Type', 'application/json')
        file_ = self.file_service.get_file_by_file_id(file_id)
        self.write(file_)
        self.finish()

class FileDataHandler(BaseHandler):
    file_service = syringe.inject('file-service')

    def post(self, user_id, file_id):
        self.set_header('Content-Type', 'application/json')

        data = tornado.escape.json_decode(self.request.body)
        file_ = self.file_service.update_file_data(
            user_id=user_id,
            file_id = file_id,
            text = data['text']
        )
        if file_:
            self.write(json.dumps(file_))
        else:
            self.send_error(
                400,
                message='File Creation failed.'
            )
        self.finish()
