# encoding: utf-8

from __future__ import absolute_import

import syringe
import bcrypt
import socket
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
import os


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
        auth = self.request.headers.get('Authorization')
        if auth and auth.startswith('Basic '):
            auth_token, refresh_token, user_id= auth.split(':')
            _, auth_token = auth_token.split(' ')
            authenticated = self.auth_service.validate_auth_token(
                user_id=user_id,
                auth_token=auth_token,
                refresh_token=refresh_token
            )
            if authenticated:
                logging.info('User successfully authenticated')
                f(self, *args, **kwargs)
            else:
                raise tornado.web.HTTPError(401, 'User not authenticated, '
                                                 'aborting')
        else:
            raise tornado.web.HTTPError(401, 'User not authenticated, '
                                             'aborting')
    return wrapper


class BaseHandler(tornado.web.RequestHandler):
    auth_service = syringe.inject('auth-service')

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request)

    def set_default_headers(self):
        if '/download' in self.request.uri:
            print('Download')
        else:
            self.set_header("Access-Control-Allow-Origin", self.request.headers['Origin'])
            self.set_header("Access-Control-Allow-Credentials", "true")
            self.set_header("Access-Control-Allow-Methods", "POST, GET, PUT, DELETE, OPTIONS")
            self.set_header("Access-Control-Allow-Headers", "X-Requested-With,Content-Type,Accept,Origin,Authorization")

    @tornado.web.asynchronous
    def options(self, *args, **kwargs):
        """XHR cross-domain OPTIONS handler"""
        self.set_status(204)
        self.finish()

    def get_login_url(self):
        return u"/login"

    def set_current_user(self, user):
        if user:
            tokens = self.auth_service.generate_oauth2_token()
            user['auth_token'] = tokens['auth_token']
            user['refresh_token'] = tokens['refresh_token']
            user['user_id'] = str(user['_id'])
            self.auth_service.generate_aut_token(**user)
            # self.set_secure_cookie("user", tornado.escape.json_encode(user), 10)
        else:
            self.clear_cookie("user")

    def write_error(self, status_code, **kwargs):
        if 'message' not in kwargs:
            kwargs['message'] = 'Done...! '
        self.write(kwargs['message'])

    @authenticated_async
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

    @tornado.web.asynchronous
    def post(self):
        self.set_header('Content-Type', 'application/json')
        email = self.get_argument('email', '')
        name = self.get_argument('name', '')
        if self.user_service.get_user_by_email(email):
            self.send_error(
                401,
                message='User already exists.'
            )
        else:
            password = self.get_argument('password', '').encode('utf-8')
            user = self.user_service.create_user(
                name=name,
                email=email,
                password=password,
                db=self.application.syncdb
            )
            if user:
                self.set_current_user(user)
                del user['password_hash']
                self.write(json.dumps(user))
            else:
                raise tornado.web.HTTPError(400, 'Registration Failed, '
                                             'aborting')
            self.finish()


class LoginHandler(BaseHandler):
    user_service = syringe.inject('user-service')

    # @tornado.web.asynchronous // dose not all
    def post(self):
        email = self.get_argument('email', '')
        password = self.get_argument('password', '').encode('utf-8')
        user = self.user_service.get_user_by_email(email)
        self.set_header('Content-Type', 'application/json')
        # Warning bcrypt will block IO loop:
        if user and user['password_hash'] and bcrypt.hashpw(password, user['password_hash']) == user['password_hash']:
            self.set_current_user(user)
            del user['password_hash']
            self.write(json.dumps(user))
        else:

            self.set_secure_cookie('flash', "Login incorrect")
            self.send_error(
                401,
                message='Login failed, email or password incorrect.'
            )


class LogoutHandler(BaseHandler):
    def post(self):
        self.clear_cookie("user")
        self.finish()


class DirectoryHandler(BaseHandler):
    dir_service = syringe.inject('directory-service')

    # @tornado.web.asynchronous
    @authenticated_async
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

    @tornado.web.asynchronous
    @authenticated_async
    def put(self, dir_id):
        self.set_header('Content-Type', 'application/json')

        data = tornado.escape.json_decode(self.request.body)
        file_ = self.dir_service.update_directory_meta(
            folder_name=data['folder_name'],
            dir_id=dir_id
        )
        if file_:
            self.write(json.dumps(file_))
        else:
            self.send_error(
                400,
                message='Directory Update failed.'
            )
        self.finish()

    @tornado.web.asynchronous
    @authenticated_async
    def delete(self, dir_id):
        self.set_header('Content-Type', 'application/json')
        dir_ =  self.dir_service.delete_directory_by_id(dir_id)
        if dir_:
            self.write(json.dumps(dir_))
        else:
            self.send_error(
                400,
                message='File Update failed.'
            )
        self.finish()


class ContentHandler(BaseHandler):
    con_service = syringe.inject('content-service')

    # @tornado.web.asynchronous
    @authenticated_async
    def get(self, user_id, dir_id):
        self.set_header('Content-Type', 'application/json')
        content = self.con_service.list_content_by_dir_id(
            user_id=user_id,
            dir_id=dir_id
        )
        self.write(json.dumps([c for c in content]))
        self.finish()

    @authenticated_async
    def put(self, con_id, dumy):
        self.set_header('Content-Type', 'application/json')
        content = self.con_service.restore_content(con_id)
        self.write(json.dumps(content))
        self.finish()


class BinHandler(BaseHandler):
    bin_service = syringe.inject('bin-service')

    # @tornado.web.asynchronous
    @authenticated_async
    def get(self, user_id):
        self.set_header('Content-Type', 'application/json')
        content = self.bin_service.list_deleted_content(
            user_id=user_id
        )
        self.write(json.dumps([c for c in content]))
        self.finish()

    @tornado.web.asynchronous
    @authenticated_async
    def delete(self, con_id):
        self.set_header('Content-Type', 'application/json')
        dir_ =  self.bin_service.delete_content(con_id)
        if dir_:
            self.write(json.dumps(dir_))
        else:
            self.send_error(
                400,
                message='File Update failed.'
            )
        self.finish()


class FileHandler(BaseHandler):
    file_service = syringe.inject('file-service')

    @tornado.web.asynchronous
    @authenticated_async
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

    @tornado.web.asynchronous
    @authenticated_async
    def put(self, file_id):
        self.set_header('Content-Type', 'application/json')

        data = tornado.escape.json_decode(self.request.body)
        file_ = self.file_service.update_file_meta(
            file_name=data['file_name'],
            file_id=file_id
        )
        if file_:
            self.write(json.dumps(file_))
        else:
            self.send_error(
                400,
                message='File Update failed.'
            )
        self.finish()

    @tornado.web.asynchronous
    @authenticated_async
    def delete(self, file_id):
        self.set_header('Content-Type', 'application/json')
        file_ =  self.file_service.delete_file_by_id(file_id)
        if file_:
            self.write(json.dumps(file_))
        else:
            self.send_error(
                400,
                message='File Update failed.'
            )
        self.finish()


    @tornado.web.asynchronous
    @authenticated_async
    def get(self, file_id):
        self.set_header('Content-Type', 'application/json')
        file_ = self.file_service.get_file_by_file_id(file_id)
        self.write(file_)
        self.finish()

class FileDataHandler(BaseHandler):
    file_service = syringe.inject('file-service')

    @tornado.web.asynchronous
    @authenticated_async
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

class CloneHandler(BaseHandler):
    con_service = syringe.inject('content-service')

    @tornado.web.asynchronous
    @authenticated_async
    def post(self):
        self.set_header('Content-Type', 'application/json')

        data = tornado.escape.json_decode(self.request.body)
        # print(data)
        res = self.con_service.clone(**data)
        if res:
            self.write(json.dumps(res))
        else:
            self.send_error(
                400,
                message='Copying data failed'
            )
        self.finish()

class ShareHandler(BaseHandler):
    share_service = syringe.inject('share-service')
    user_service = syringe.inject('user-service')

    @tornado.web.asynchronous
    @authenticated_async
    def post(self, user_id):
        # self.set_header('Content-Type', 'application/json')

        data = tornado.escape.json_decode(self.request.body)
        user = self.user_service.get_user_by_email(data['email'])
        if not user:
            self.send_error(
                401,
                message='File canot be shared User : {} does not exist'.format(data['email'])
            )
        data['user_id'] = str(user['_id'])
        res = self.share_service.create_share_repo(**data)
        if res:
            self.write("Directory has been shared with {}".format(user['user_name']))
        else:
            self.send_error(
                400,
                message='Sharing data failed'
            )
        self.finish()

    @authenticated_async
    def get(self, user_id):
        self.set_header('Content-Type', 'application/json')
        content = self.share_service.list_shared_content(
            user_id=user_id
        )
        self.write(json.dumps([c for c in content]))
        self.finish()

class FileDownloadHandler(BaseHandler):
    file_service = syringe.inject('file-service')
    # @authenticated_async
    def get(self, file_id):

        file_ = self.file_service.get_file_by_file_id(file_id)
        file_name = file_['file_name']
        _file_dir = os.path.abspath("")+"/src/tmp"
        _file_path = "%s/%s" % (_file_dir, file_name)
        tmp = open(_file_path, 'w')
        tmp.write(file_['text'])
        tmp.close()
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % file_name)
        with open(_file_path, "rb") as f:
            try:
                while True:
                    _buffer = f.read(4096)
                    if _buffer:
                        self.write(_buffer)
                    else:
                        f.close()
                        self.finish()
                        return
            except:
                raise HTTPError(404)
        raise HTTPError(500)

class UploadFileHandler(BaseHandler):

    file_service = syringe.inject('file-service')
    # @authenticated_async
    # @tornado.web.asynchronous
    def post(self, user_id, parent_id):
        try:
            self.set_header('Content-Type', 'application/json')
            file1 = self.request.files['file'][0]

            dir_ = self.file_service.create_new_file(
                user_id=user_id,
                file_name=file1['filename'],
                text=file1['body'].decode("utf-8"),
                parent_dir_id=parent_id,
                contributors=['']
            )
            if dir_:
                self.write(json.dumps(dir_))
        except:
            self.send_error(
                400,
                message='File upload failed! kindly check your file for errors and try again.'
            )
