# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt
import logging
import unittest

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

from golink import model
from golink import views


class TestDatabase:
    def __init__(self):
        self.golinks = {}

    def find_golink_by_name(self, name: str):
        logging.info('find_golink_by_name: %s', name)
        return self.golinks[name]

    def insert_or_replace_golink(self, golink: model.Golink):
        logging.info('insert_or_replace_golink: %s', golink)
        self.golinks[golink.name] = golink


class ViewsTestCase(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app['DATABASE'] = TestDatabase()
        app.router.add_routes(views.routes)
        return app

    @property
    def database(self):
        return self.app['DATABASE']

    def add_golink_url(self, name, url):
        """Add Golink URL to database."""
        self.database.insert_or_replace_golink(model.Golink(name, url))

    @unittest_run_loop
    async def test_golink_redirect(self):
        self.add_golink_url('test', 'http://www.example.com/foo/')

        resp = await self.client.request('GET', '/test', allow_redirects=False)  # type: web.Response
        self.assertEqual(web.HTTPFound.status_code, resp.status)
        self.assertEqual('http://www.example.com/foo/', resp.headers['Location'])

    @unittest_run_loop
    async def test_unknown_golink_redirect(self):
        resp = await self.client.request('GET', '/test', allow_redirects=False)  # type: web.Response
        self.assertEqual(web.HTTPSeeOther.status_code, resp.status)
        self.assertEqual('/test?edit', resp.headers['Location'])

    @unittest_run_loop
    async def test_golink_with_path_redirect(self):
        self.add_golink_url('test', 'http://www.example.com/foo/')

        resp = await self.client.request('GET', '/test/bar', allow_redirects=False)  # type: web.Response
        self.assertEqual(web.HTTPFound.status_code, resp.status)
        self.assertEqual('http://www.example.com/foo/bar', resp.headers['Location'])

    @unittest_run_loop
    async def test_golink_with_partial_path_redirect(self):
        self.add_golink_url('test', 'http://www.example.com/foo')

        resp = await self.client.request('GET', '/test/bar', allow_redirects=False)  # type: web.Response
        self.assertEqual(web.HTTPFound.status_code, resp.status)
        self.assertEqual('http://www.example.com/foobar', resp.headers['Location'])

    @unittest_run_loop
    async def test_post_golink(self):
        resp = await self.client.request('POST', '/test', data={'name': 'test', 'url': 'http://www.example.com/post'},
                                         allow_redirects=False)  # type: web.Response
        self.assertEqual({'test': model.Golink('test', 'http://www.example.com/post')}, self.database.golinks)
        self.assertEqual(web.HTTPSeeOther.status_code, resp.status)
        self.assertEqual('/test?edit', resp.headers['Location'])

    @unittest_run_loop
    async def test_post_golink_with_suffix(self):
        resp = await self.client.request('POST', '/test/x', data={'name': 'test', 'url': 'http://www.example.com/post'},
                                         allow_redirects=False)  # type: web.Response
        self.assertEqual(web.HTTPMethodNotAllowed.status_code, resp.status)

    @unittest_run_loop
    async def test_favicon(self):
        resp = await self.client.request('GET', '/favicon.ico', allow_redirects=False)  # type: web.Response
        self.assertEqual(web.HTTPNotFound.status_code, resp.status)

    @unittest_run_loop
    async def test_robots_txt(self):
        resp = await self.client.request('GET', '/robots.txt', allow_redirects=False)  # type: web.Response
        self.assertEqual(web.HTTPOk.status_code, resp.status)
        self.assertEqual('User-agent: *\nDisallow: /\n', await resp.text())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
