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

    def render_template(self, name, context):
        full_context = dict({'auth': self.auth}, **context)
        return aiohttp_jinja2.render_template(name, self.request, full_context)

    def url_for_name(self, name) -> yarl.URL:
        return self.request.app.router['golink'].url_for(name=name)


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

        name = post['name'].strip()
        try:
            validate_name(name)
        except ValueError as e:
            raise web.HTTPBadRequest(text='Invalid Golink: {}'.format(e))

        raise web.HTTPSeeOther(self.url_for_name(name).with_query('edit'))


@routes.view('/{{name:{0}}}'.format(NAME_RE.pattern), name='golink')
class GolinkView(GolinkBaseView):
    """Handles bare Golinks (e.g. go/name)."""

    async def get(self):
        name = self.request.match_info['name']

        try:
            golink = self.database.find_golink_by_name(name)
        except KeyError:
            golink = None

        if 'edit' in self.request.query:
            # Only edit if no suffix after name (e.g. http://go/name?edit)
            if golink:
                return self.render_template('edit.html', {'golink': golink})
            else:
                return self.render_template('create.html', {'name': name})
        elif not golink:
            # Redirect to edit view
            raise web.HTTPSeeOther(self.url_for_name(name).with_query('edit'))
        else:
            raise web.HTTPFound(golink.url)

    async def post(self):
        self.require_authentication()

        name = self.request.match_info['name'].strip()
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
        raise web.HTTPSeeOther(self.url_for_name(name).with_query('edit'))


@routes.view('/{{name:{0}}}/{{suffix:[^{{}}]*}}'.format(NAME_RE.pattern), name='golink_with_suffix')
class GolinkWithSuffixView(GolinkBaseView):
    """Handles Golinks with a suffix (e.g. go/name/suffix)."""

    async def get(self):
        name = self.request.match_info['name']
        suffix = self.request.match_info['suffix']

        try:
            golink = self.database.find_golink_by_name(name)
        except KeyError:
            # Redirect to edit view
            raise web.HTTPSeeOther(self.url_for_name(name).with_query('edit'))

        raise web.HTTPFound(golink.with_suffix(suffix))
