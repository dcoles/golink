# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt
import aiohttp_jinja2
import yarl
from aiohttp import web

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

    @property
    def database(self) -> persistence.Database:
        return self.request.app['DATABASE']

    @property
    def name(self):
        """Golink name from URL."""
        return self.request.match_info['name'].lower()

    def render_template(self, name, context={}):
        full_context = dict({'auth': self.auth}, **context)
        return aiohttp_jinja2.render_template(name, self.request, full_context)

    def url_for_name(self, name) -> yarl.URL:
        return self.request.app.router['golink'].url_for(name=name)

    def url_for_edit(self, name) -> yarl.URL:
        return self.request.app.router['edit'].url_for(name=name)


@routes.view('/')
class IndexView(GolinkBaseView):
    """Handles index requests."""

    async def get(self):
        golinks = list(self.database.golinks_by_owner(self.auth.current_user()))
        return self.render_template('index.html', {'golinks': golinks})

    async def post(self):
        post = await self.request.post()
        missing = [key for key in ('name',) if key not in post]
        if missing:
            raise web.HTTPBadRequest(text='Missing required field: {}'.format(' '.join(missing)))

        name = post['name'].lower()
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

        return self.render_template('search.html', {'query': query, 'golinks': self.database.search(query)})


@routes.view('/+edit/{{name:{0}}}'.format(NAME_RE.pattern), name='edit')
class EditView(GolinkBaseView):
    """Handles editing Golinks."""

    async def get(self):
        name = self.name

        try:
            golink = self.database.find_golink_by_name(name)
        except KeyError:
            return self.render_template('create.html', {'name': name})

        return self.render_template('edit.html', {'golink': golink})

    async def post(self):
        self.require_authentication()

        name = self.name
        post = await self.request.post()

        missing = [key for key in ('url', ) if key not in post]
        if missing:
            raise web.HTTPBadRequest(text='Missing required field: {}'.format(' '.join(missing)))

        try:
            current_golink = self.database.find_golink_by_name(name)
        except KeyError:
            if not self.auth.can_create():
                raise web.HTTPForbidden()
        else:
            if not self.auth.can_edit(current_golink):
                raise web.HTTPForbidden()

        url = post['url'].strip()

        try:
            golink = Golink(name, url, self.auth.current_user())
        except ValueError as e:
            raise web.HTTPBadRequest(text='Invalid Golink: {}'.format(e))
        self.database.insert_or_replace_golink(golink)

        # Redirect to edit view
        raise web.HTTPSeeOther(self.url_for_edit(name))


@routes.view('/{{name:{0}}}'.format(NAME_RE.pattern), name='golink')
class GolinkView(GolinkBaseView):
    """Handles bare Golinks (e.g. go/name)."""

    async def get(self):
        name = self.name

        try:
            golink = self.database.find_golink_by_name(name)
        except KeyError:
            # Redirect to edit view
            raise web.HTTPSeeOther(self.url_for_edit(name))

        raise web.HTTPFound(golink.url)


@routes.view('/{{name:{0}}}/{{suffix:[^{{}}]*}}'.format(NAME_RE.pattern), name='golink_with_suffix')
class GolinkWithSuffixView(GolinkBaseView):
    """Handles Golinks with a suffix (e.g. go/name/suffix)."""

    async def get(self):
        name = self.name
        suffix = self.request.match_info['suffix']

        try:
            golink = self.database.find_golink_by_name(name)
        except KeyError:
            # Redirect to edit view
            raise web.HTTPSeeOther(self.url_for_edit(name))

        raise web.HTTPFound(golink.with_suffix(suffix))
