from __future__ import absolute_import

import socket
import base64
import uuid
import tornado
from tornado import httpserver, netutil
import tornado.wsgi
import wsgiref.simple_server
from tornado.web import url
from tornado.options import define
from tornado.options import options
from pymongo import MongoClient

from src.mongolayer import mongodb as db_handlers
from src import services
from src import api


define('port', default=8901, type=int)

try:
    _ip = socket.gethostbyname(socket.gethostname())

    if _ip.startswith("127."):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 0))  # address doesn't send packets
        _ip = s.getsockname()[0]

except:
    print('Network is down falling back to the local host.')
    _ip = 'localhost'

define('address', _ip)


MONGO_SERVER = 'localhost'


def init_services():
    """
    Initialise the services used by the core framework.

    """
    services.UserService()

def init_db_handlers(app):
    db_handlers.MongoDbHandler(app)


class Application(tornado.wsgi.WSGIApplication):
    def __init__(self, **kwars):
        handlers = [
            url(r"/", api.BaseHandler),
            url(r"/api/login", api.LoginHandler),
            url(r"/api/register", api.RegisterHandler)
            # url(r"/logout", api.LogoutHandler)
        ]

        settings = {
            'cookie_secret': self.gen_uniq_id(),
            'debug': False,
            'autoreload': True
        }

        tornado.web.Application.__init__(self, handlers, **settings)
        self.syncconnection = MongoClient(MONGO_SERVER, 27017, connect=False)

        if 'db' in kwars:
            self.syncdb = self.syncconnection[kwars['db']]
        else:
            self.syncdb = self.syncconnection['yo-db']

    def gen_uniq_id(self, num_bytes=16):
        return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    sockets = tornado.netutil.bind_sockets(options.port, address=options.address)
    # tornado.process.fork_processes(0) does not work on windows
    app = Application()
    init_services()
    init_db_handlers(app)
    server = httpserver.HTTPServer(app)
    server.add_sockets(sockets)

    print('Web server is listing at :' + options.address + ':' + str(options.port))
    tornado.ioloop.IOLoop.instance().start()
