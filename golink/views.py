# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt
import aiohttp_jinja2
import yarl
from aiohttp import web

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
    def readonly(self):
        return self.request.app.get('READONLY', False)

    def requires_edit_permission(self):
        if self.readonly:
            raise web.HTTPForbidden()

    @property
    def database(self):
        return self.request.app['DATABASE']

    def url_for_name(self, name) -> yarl.URL:
        return self.request.app.router['golink'].url_for(name=name)


@routes.view('/')
class IndexView(GolinkBaseView):
    """Handles index requests."""

    @aiohttp_jinja2.template('index.html')
    async def get(self):
        golinks = list(self.database.golinks())
        return {'golinks': golinks, 'readonly': self.readonly}

    async def post(self):
        self.requires_edit_permission()

        post = await self.request.post()
        missing = [key for key in ('name', 'url') if key not in post]
        if missing:
            raise web.HTTPBadRequest(text='Missing required field: {}'.format(' '.join(missing)))

        name = post['name'].strip()
        try:
            validate_name(name)
        except ValueError as e:
            raise web.HTTPBadRequest(text='Invalid Golink: {}'.format(e))

        raise web.HTTPTemporaryRedirect(self.url_for_name(name))


@routes.view('/{{name:{0}}}'.format(NAME_RE.pattern), name='golink')
class GolinkView(GolinkBaseView):
    """Handles bare Golinks (e.g. go/name)."""

    @aiohttp_jinja2.template('edit.html')
    async def get(self):
        name = self.request.match_info['name']

        try:
            golink = self.request.app['DATABASE'].find_golink_by_name(name)
        except KeyError:
            golink = None

        url = golink.url if golink else ''

        if 'edit' in self.request.query:
            # Only edit if no suffix after name (e.g. http://go/name?edit)
            return {
                'golink_name': name,
                'golink_url': url,
                'readonly': self.readonly,
            }
        elif not golink:
            # Redirect to edit view
            raise web.HTTPSeeOther(self.url_for_name(name).with_query('edit'))
        else:
            raise web.HTTPFound(golink.url)

    async def post(self):
        self.requires_edit_permission()

        name = self.request.match_info['name'].strip()
        post = await self.request.post()

        missing = [key for key in ('url', ) if key not in post]
        if missing:
            raise web.HTTPBadRequest(text='Missing required field: {}'.format(' '.join(missing)))

        url = post['url'].strip()

        try:
            golink = Golink(name, url)
        except ValueError as e:
            raise web.HTTPBadRequest(text='Invalid Golink: {}'.format(e))
        self.request.app['DATABASE'].insert_or_replace_golink(golink)

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
