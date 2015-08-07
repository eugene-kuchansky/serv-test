#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os, os.path, sys
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
from tornado.httpclient import HTTPRequest
from tornado.httputil import HTTPHeaders
import json
from time import sleep
import logging
import unittest

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

from settings import X_AUTH_TOKEN
from serv import handlers
from models import Server, init_db, clear_db

# disable tornado WARNINGS
null_logger = logging.NullHandler()
null_logger.setLevel(logging.DEBUG)
logging.getLogger("tornado.access").addHandler(null_logger)
logging.getLogger("tornado.access").propagate = False


init_db()

app = Application(handlers)
app.listen(9999)

   
class ServerTest(AsyncHTTPTestCase):
    
    def get_app(self):
        return Application(handlers)

    def test_root(self):
        """
        dummy test root
        """
        self.http_client.fetch(self.get_url('/'), self.stop)
        response = self.wait()

        assert json.loads(response.body) == {'status': 'test'}

    def test_unauth(self):
        """
        Test with incorrect token
        """

        request = HTTPRequest(
            self.get_url('/1/servers/'),
            method='GET',
            headers=HTTPHeaders({'X-AUTH-TOKEN': 'wrong token'}),
        )

        self.http_client.fetch(request, self.stop)
        response = self.wait()

        assert json.loads(response.body) == {'message': 'restricted'}

    def test_list(self):
        """
        list of servers
        """
        clear_db()
        s1 = Server.create(server_id=None, tenant_id=1, name='name1', status='ready')
        s2 = Server.create(server_id=None, tenant_id=1, name='name2', status='scheduled')
        Server.create(server_id=None, tenant_id=2, name='name3', status='ready')

        request = HTTPRequest(
            self.get_url('/1/servers/'),
            method='GET',
            headers=HTTPHeaders({'X-AUTH-TOKEN': X_AUTH_TOKEN}),
        )

        self.http_client.fetch(request, self.stop)
        response = self.wait()
        message = json.loads(response.body)

        assert message == {'servers': [
            {'status': s1.status, 'id': s1.server_id, 'name': s1.name},
            {'status': s2.status, 'id': s2.server_id, 'name': s2.name},
        ]}

    def test_view(self):
        """
        test getting one server
        """
        clear_db()
        s1 = Server.create(server_id=None, tenant_id=1, name='name1', status='ready')
        Server.create(server_id=None, tenant_id=1, name='name2', status='scheduled')
        Server.create(server_id=None, tenant_id=2, name='name3', status='ready')

        request = HTTPRequest(
            self.get_url('/1/servers/' + str(s1.server_id)),
            method='GET',
            headers=HTTPHeaders({'X-AUTH-TOKEN': X_AUTH_TOKEN}),
        )

        self.http_client.fetch(request, self.stop)
        response = self.wait()
        message = json.loads(response.body)

        assert message == {
            'status': s1.status, 'id': s1.server_id, 'name': s1.name, 'date_created': str(s1.date_created)
        }

    def test_view_not_found(self):
        """
        test view non existing server
        """
        clear_db()

        request = HTTPRequest(
            self.get_url('/1/servers/1'),
            method='GET',
            headers=HTTPHeaders({'X-AUTH-TOKEN': X_AUTH_TOKEN}),
        )

        self.http_client.fetch(request, self.stop)
        response = self.wait()
        message = json.loads(response.body)
        assert message == {'status': 'not_found'}

    def test_delete_not_found(self):
        """
        try to delete non existing server
        """
        clear_db()

        request = HTTPRequest(
            self.get_url('/1/servers/1'),
            method='DELETE',
            headers=HTTPHeaders({'X-AUTH-TOKEN': X_AUTH_TOKEN}),
        )

        self.http_client.fetch(request, self.stop)
        response = self.wait()
        message = json.loads(response.body)
        assert message == {'status': 'not_found'}

    def test_delete(self):
        """
        delete existing server
        """
        clear_db()
        s1 = Server.create(server_id=None, tenant_id=1, name='name1', status='ready')

        request = HTTPRequest(
            self.get_url('/1/servers/' + str(s1.server_id)),
            method='DELETE',
            headers=HTTPHeaders({'X-AUTH-TOKEN': X_AUTH_TOKEN}),
        )

        self.http_client.fetch(request, self.stop)
        response = self.wait()
        message = json.loads(response.body)
        assert message == {'status': 'deleted', 'id': s1.server_id}

    def test_create_invalid_name(self):
        """
        try to create server with too short name
        """
        clear_db()

        request = HTTPRequest(
            self.get_url('/1/servers/create'),
            method='POST',
            headers=HTTPHeaders({'X-AUTH-TOKEN': X_AUTH_TOKEN}),
            body='name=test'
        )

        self.http_client.fetch(request, self.stop)
        response = self.wait()
        message = json.loads(response.body)

        assert message == {'status': 'invalid_name'}

    def test_create_server(self):
        """
        try to create server with too short name
        """
        clear_db()
        server_name = 'server1'

        request = HTTPRequest(
            self.get_url('/1/servers/create'),
            method='POST',
            headers=HTTPHeaders({'X-AUTH-TOKEN': X_AUTH_TOKEN}),
            body='name=%s' % server_name
        )

        self.http_client.fetch(request, self.stop)
        response = self.wait()
        message = json.loads(response.body)
        assert message['status'] == 'pending'
        assert message['name'] == 'server1'
        server_id = message['id']
        sleep(1)
        for status in ('scheduled', 'processing', 'ready'):
            sleep(10)
            request = HTTPRequest(
                self.get_url('/1/servers/' + str(server_id)),
                method='GET',
                headers=HTTPHeaders({'X-AUTH-TOKEN': X_AUTH_TOKEN}),
            )

            self.http_client.fetch(request, self.stop)
            response = self.wait()
            message = json.loads(response.body)

            assert message['status'] == status


if __name__ == '__main__':
    unittest.main()