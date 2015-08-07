#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from tornado.ioloop import IOLoop
from tornado.web import Application, url
import tornado.gen
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from models import Server, DbHandler, db, init_db
from settings import X_AUTH_TOKEN

tpe = ThreadPoolExecutor(max_workers=10)


def simple_auth(func):
    def func_wrapper(*args, **kwargs):
        self = args[0]
        auth_hdr = self.request.headers.get('X-AUTH-TOKEN')
        if auth_hdr is None or auth_hdr != X_AUTH_TOKEN:
            self.set_status(401)
            self.set_header('Authenticate', 'X-AUTH-TOKEN')
            self.write({'message': 'restricted'})
            self.finish()
            return
        return func(*args, **kwargs)
    return func_wrapper


class ListServersHandler(DbHandler):
    @simple_auth
    def get(self, tenant_id):
        servers = [
            {
                'id': server.server_id,
                'name': server.name,
                'status': server.status,
            }
            for server in Server.select(Server.server_id, Server.name, Server.status).where(Server.tenant_id == tenant_id).order_by(Server.server_id)
        ]
        self.write({'servers': servers})


class ServerHandler(DbHandler):
    @simple_auth
    def get(self, tenant_id, server_id):
        try:
            server = Server.get(Server.tenant_id == tenant_id, Server.server_id == server_id)
        except Server.DoesNotExist:
            self.write({'status': 'not_found'})
            return

        self.write({
            'id': server.server_id,
            'name': server.name,
            'status': server.status,
            'date_created': str(server.date_created),
        })

    @simple_auth
    def delete(self, tenant_id, server_id):
        try:
            server = Server.get(Server.tenant_id == tenant_id, Server.server_id == server_id)
        except Server.DoesNotExist:
            self.write({'status': 'not_found'})
            return
        server.delete_instance()

        self.write({
            'id': int(server_id),
            'status': 'deleted',
        })


def make_task(server_id, status):
    sleep(10)
    db.connect()
    try:
        server = Server.get(Server.server_id == server_id)
    except Server.DoesNotExist:
        db.close()
        return False
    server.status = status
    server.save()
    db.close()
    return True


def create_server(server_id):
    for status in ('scheduled', 'processing', 'ready'):
        if not make_task(server_id, status):
            return


class CreateServerHandler(DbHandler):
    @simple_auth
    def post(self, tenant_id):
        name = self.get_argument('name')
        if not 20 >= len(name) >= 5:
            self.write({'status': 'invalid_name'})
            return

        server = Server.create(
            server_id=None,
            tenant_id=tenant_id,
            name=name,
        )

        IOLoop.current().spawn_callback(self.run_task, server.server_id)

        self.write({
            'id': server.server_id,
            'name': server.name,
            'status': server.status,
        })

    @tornado.gen.coroutine
    def run_task(self, server_id):
        tpe.submit(
            partial(create_server, server_id)
        )


class DefaultHandler(DbHandler):
    def get(self):
        self.write({
            'status': 'test'
        })


handlers = [
    url(r'/', DefaultHandler),
    url(r'/([0-9]+)/servers/', ListServersHandler),
    url(r'/([0-9]+)/servers/([0-9]+)', ServerHandler),
    url(r'/([0-9]+)/servers/create', CreateServerHandler),
]


if __name__ == "__main__":
    init_db()
    app = Application(handlers)
    app.listen(8888)
    IOLoop.current().start()
