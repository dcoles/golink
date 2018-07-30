# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt
from urllib.parse import urlsplit

import aiohttp_jinja2
import yarl
from aiohttp import web
import posixpath

from golink import auth
from golink import persistence
from golink.model import Golink, validate_name, NAME_RE

routes = web.RouteTableDef()


@routes.get('/favicon.ico')
async def get_favicon_ico(request: web.Request):
    # No favicon
    raise web.HTTPNotFound()


@routes.get('/robots.txt')
async def get_robots_txt(request: web.Request):
    # Disallow all robots
    return web.Response(text='User-agent: *\nDisallow: /\n', content_type='text/plain')


class GolinkBaseView(web.View):
    @property
    def auth(self) -> auth.Auth:
        # Cache authenticator per request
        if 'AUTH' not in self.request:
            auth_type = self.request.app['AUTH_TYPE']
            self.request['AUTH'] = auth_type(self.request)

        return self.request['AUTH']

    def require_authentication(self):
        """
        Require the user to be authenticated.

        :throws web.HTTPForbidden: If unable to authenticate the current user.
        """
        if not self.auth.authenticated:
            raise web.HTTPForbidden()

    def require_fields(self, fields, required):
        """
        Require fields.

        :param fields: Mapping of fields sent by client.
        :param required: List of required fields.
        :return: Values of required fields.
        :throws web.HTTPBadRequest: If require field is missing
        """
        missing = [key for key in required if key not in fields or not fields[key]]
        if missing:
            raise web.HTTPBadRequest(text='Missing required field(s): {}'.format(' '.join(missing)))

        return tuple(fields[key] for key in required)

    @property
    def database(self) -> persistence.Database:
        return self.request.app['DATABASE']

    @property
    def name(self):
        """Get Golink name from path."""
        if 'name' not in self.request:
            self.set_request_name_and_suffix_from_path()

        return self.request['name']

    @property
    def suffix(self):
        if 'suffix' not in self.request:
            self.set_request_name_and_suffix_from_path()

        return self.request['suffix']

    def set_request_name_and_suffix_from_path(self):
        """Get Golink name and optional suffix from path."""
        path = self.request.match_info['path']
        self.request['name'], self.request['suffix'] = self.split_path(path)

    def split_path(self, path):
        """Split a Golink path into name and optional suffix."""
        try:
            name, suffix = path.split('/', 1)
        except ValueError:
            name, suffix = path, ''

        return name.lower(), suffix

    def validate_name(self):
        """Validate name.

        :raises web.HTTPNotFound: if name is invalid.
        """
        try:
            validate_name(self.name)
        except ValueError as e:
            raise web.HTTPNotFound(text=f'Invalid Golink name: {e}')

    def render_template(self, name, context={}):
        full_context = dict({'auth': self.auth}, **context)
        return aiohttp_jinja2.render_template(name, self.request, full_context)

    async def handle_golink(self, name, suffix=None):
        try:
            golink = await self.database.find_by_name(name)
        except KeyError:
            # Redirect to edit view
            raise web.HTTPSeeOther(self.url_for_edit(name))

        await self.database.increment_visits(name)
        url = golink.with_suffix(suffix) if suffix else golink.url
        raise web.HTTPFound(url)

    def url_for_name(self, name, suffix=None) -> yarl.URL:
        validate_name(name)
        path = posixpath.join(name, suffix) if suffix else name
        return self.request.app.router['golink'].url_for(path=path)

    def url_for_edit(self, name) -> yarl.URL:
        validate_name(name)
        return self.request.app.router['edit'].url_for(path=name)

    def url_for_search(self, query) -> yarl.URL:
        return self.request.app.router['search'].url_for().with_query({'q': query})


@routes.view('/')
class IndexView(GolinkBaseView):
    """Handles index requests."""

    async def get(self):
        golinks = list(await self.database.find_by_owner(self.auth.current_user()))
        return self.render_template('index.html', {'golinks': golinks})

    async def post(self):
        post = await self.request.post()
        name, = self.require_fields(post, ('name',))

        name = name.lower()
        try:
            validate_name(name)
        except ValueError as e:
            raise web.HTTPBadRequest(text='Invalid Golink: {}'.format(e))

        raise web.HTTPSeeOther(self.url_for_edit(name))


@routes.view('/+search', name='search')
class SearchView(GolinkBaseView):
    """Handles searching Golinks."""

    async def get(self):
        query = self.request.query.get('q')

        if not query:
            return self.render_template('search.html')

        return self.render_template('search.html', {'query': query, 'golinks': await self.database.search(query)})

    async def post(self):
        post = await self.request.post()

        action, query = self.require_fields(post, ('action', 'q'))
        if action in ('go', 'edit'):
            u = urlsplit(query)
            name, suffix = self.split_path(u.path)
            try:
                if u.scheme or u.hostname:
                    raise ValueError('Must not be a full URL')
                validate_name(name)
            except ValueError as e:
                raise web.HTTPBadRequest(text=f'Invalid Golink name: {e}')
            if action == 'edit':
                url = self.url_for_edit(name)
            else:
                url = self.url_for_name(name, suffix).with_fragment(u.fragment)
            raise web.HTTPSeeOther(url)
        elif action == 'search':
            raise web.HTTPSeeOther(self.url_for_search(query))
        else:
            raise web.HTTPBadRequest(text='`action` must be either "go" or "search"')


@routes.view('/+edit/{path}', name='edit')
class EditView(GolinkBaseView):
    """View for editing Golinks."""

    async def get(self):
        try:
            golink = await self.database.find_by_name(self.name)
        except KeyError:
            return self.render_template('create.html', {'name': self.name})

        return self.render_template('edit.html', {'golink': golink})

    async def post(self):
        self.require_authentication()

        post = await self.request.post()

        url, = self.require_fields(post, ('url',))

        try:
            current_golink = await self.database.find_by_name(self.name)
        except KeyError:
            if not self.auth.can_create():
                raise web.HTTPForbidden()
        else:
            if not self.auth.can_edit(current_golink):
                raise web.HTTPForbidden()

        action = post.get('action')

        if action == "delete":
            await self.database.delete(self.name)
        else:
            try:
                golink = Golink(self.name, url, self.auth.current_user())
            except ValueError as e:
                raise web.HTTPBadRequest(text='Invalid Golink: {}'.format(e))
            await self.database.insert_or_replace(golink)

        # Redirect to edit view
        raise web.HTTPSeeOther(self.url_for_edit(self.name))


@routes.view('/{path:[^{}+][^{}]*}', name='golink')
class GolinkView(GolinkBaseView):
    """View for Golinks (matches any path that does not begin with `/+`)."""

    async def get(self):
        self.validate_name()
        return await self.handle_golink(self.name, self.suffix)
