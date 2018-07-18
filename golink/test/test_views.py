# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt

import logging
import unittest
from typing import Type

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

from golink import model, auth
from golink import views


class TestDatabase:
    def __init__(self):
        self.golinks = {}

    async def find_by_name(self, name: str):
        logging.info('find_by_name: %s', name)
        return self.golinks[name]

    async def insert_or_replace(self, golink: model.Golink):
        logging.info('insert_or_replace: %s', golink)
        self.golinks[golink.name] = golink

    async def increment_visits(self, name: str):
        logging.info('increment_visits: %s', name)
        self.golinks[name].visits += 1


class TestAuth(auth.Auth):
    USER = 'foo'

    def current_user(self):
        return self.USER


class BaseViewsTestCase(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app['DATABASE'] = TestDatabase()
        app['AUTH_TYPE'] = TestAuth
        app.router.add_routes(views.routes)
        return app

    @property
    def database(self):
        return self.app['DATABASE']

    async def add_golink_url(self, name='test', url='http://example.com/test/', owner=TestAuth.USER):
        """Add Golink URL to database."""
        await self.database.insert_or_replace(model.Golink(name, url, owner))

    def assert_status(self, resp: web.Response, status: Type[web.HTTPException]=web.HTTPFound):
        self.assertEqual(status.status_code, resp.status)

    def assert_location(self, resp: web.Response, location='http://example.com/test/'):
        self.assertEqual(location, resp.headers['Location'])

    def assert_database(self, expected={'test': model.Golink('test', 'http://example.com/test/', TestAuth.USER)}):
        self.assertEqual(expected, self.database.golinks)

    def assert_visits(self, visits, name='test'):
        self.assertEqual(visits, self.database.golinks[name].visits)

    async def get_golink(self, path='/test') -> web.Response:
        return await self.client.request('GET', path, allow_redirects=False)

    async def post_golink(self, path='/+edit/test', url='http://example.com/test/') -> web.Response:
        return await self.client.request('POST', path, data={'url': url}, allow_redirects=False)


class ViewsTestCase(BaseViewsTestCase):
    @unittest_run_loop
    async def test_golink_redirect(self):
        await self.add_golink_url()

        resp = await self.get_golink()
        self.assert_status(resp)
        self.assert_location(resp)

    @unittest_run_loop
    async def test_unknown_golink_redirect(self):
        resp = await self.get_golink()
        self.assert_status(resp, web.HTTPSeeOther)
        self.assert_location(resp, '/+edit/test')

    @unittest_run_loop
    async def test_golink_with_path_redirect(self):
        await self.add_golink_url()

        resp = await self.get_golink('/test/foo')
        self.assert_status(resp)
        self.assert_location(resp, 'http://example.com/test/foo')
        self.assert_visits(1)

    @unittest_run_loop
    async def test_golink_with_partial_path_redirect(self):
        await self.add_golink_url(url='http://example.com/foo')

        resp = await self.get_golink('/test/bar')
        self.assert_status(resp)
        self.assert_location(resp, 'http://example.com/foobar')
        self.assert_visits(1)

    @unittest_run_loop
    async def test_multiple_visits(self):
        await self.add_golink_url()
        self.assert_visits(0)

        for visit in range(1, 11):
            resp = await self.get_golink('/test/foo')
            self.assert_status(resp)
            self.assert_visits(visit)

    @unittest_run_loop
    async def test_post_golink(self):
        resp = await self.post_golink()
        self.assert_status(resp, web.HTTPSeeOther)
        self.assert_location(resp, '/+edit/test')
        self.assert_database()

    @unittest_run_loop
    async def test_post_golink_existing(self):
        await self.add_golink_url(url='http://example.com/old/')
        self.assert_database({'test': model.Golink('test', 'http://example.com/old/', TestAuth.USER)})

        resp = await self.post_golink()
        self.assert_status(resp, web.HTTPSeeOther)
        self.assert_location(resp, '/+edit/test')
        self.assert_database()

    @unittest_run_loop
    async def test_post_golink_existing_non_owner(self):
        await self.add_golink_url(url='http://example.com/old/', owner='frank')

        resp = await self.post_golink()
        self.assert_status(resp, web.HTTPForbidden)
        self.assert_database({'test': model.Golink('test', 'http://example.com/old/', 'frank')})

    @unittest_run_loop
    async def test_post_golink_with_suffix(self):
        resp = await self.post_golink('/test/x')
        self.assert_status(resp, web.HTTPMethodNotAllowed)

    @unittest_run_loop
    async def test_favicon(self):
        resp = await self.get_golink('/favicon.ico')
        self.assert_status(resp, web.HTTPNotFound)

    @unittest_run_loop
    async def test_robots_txt(self):
        resp = await self.get_golink('/robots.txt')
        self.assert_status(resp, web.HTTPOk)
        self.assertEqual('User-agent: *\nDisallow: /\n', await resp.text())


class NullAuthViewsTestCase(BaseViewsTestCase):
    async def get_application(self):
        app = await super().get_application()
        app['AUTH_TYPE'] = auth.NullAuth
        return app

    @unittest_run_loop
    async def test_post_golink(self):
        resp = await self.post_golink()
        self.assert_status(resp, web.HTTPForbidden)
        self.assert_database({})

    @unittest_run_loop
    async def test_post_existing_golink(self):
        await self.add_golink_url(url='http://example.com/old/')

        resp = await self.post_golink()
        self.assert_status(resp, web.HTTPForbidden)
        self.assert_database({'test': model.Golink('test', 'http://example.com/old/', TestAuth.USER)})


class ReadOnlyViewsTestCase(BaseViewsTestCase):
    async def get_application(self):
        app = await super().get_application()
        app['READONLY'] = True
        return app

    @unittest_run_loop
    async def test_post_golink(self):
        resp = await self.post_golink()
        self.assert_status(resp, web.HTTPForbidden)
        self.assert_database({})

    @unittest_run_loop
    async def test_post_existing_golink(self):
        await self.add_golink_url(url='http://example.com/old')

        resp = await self.post_golink()
        self.assert_status(resp, web.HTTPForbidden)
        self.assert_database({'test': model.Golink('test', 'http://example.com/old', TestAuth.USER)})


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
