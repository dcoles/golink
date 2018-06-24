# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt

import argparse
import logging

import yarl
from aiohttp import web
import aiohttp_jinja2
import jinja2

from golink.model import Golink, validate_name, NAME_RE
from golink.persistence import Database

# TODO(dcoles) Remove once proper authentication is added
READONLY = True  # Don't set to false unless in a trusted environment


@aiohttp_jinja2.template('edit.html')
async def get_index(request: web.Request):
    """Handle index GET requests."""
    return {'readonly': READONLY}


async def post_index(request: web.Request):
    """Handle index POST requests."""
    if READONLY:
        raise web.HTTPForbidden()

    post = await request.post()
    missing = [key for key in ('name', 'url') if key not in post]
    if missing:
        raise web.HTTPBadRequest(text='Missing required field: {}'.format(' '.join(missing)))

    name = post['name'].strip()
    try:
        validate_name(name)
    except ValueError as e:
        raise web.HTTPBadRequest(text='Invalid Golink: {}'.format(e))

    raise web.HTTPTemporaryRedirect(url_for_name(request, name))


@aiohttp_jinja2.template('edit.html')
async def get_golink(request: web.Request):
    """Handle GET requests."""
    name = request.match_info['name']

    try:
        golink = request.app['DATABASE'].find_golink_by_name(name)
    except KeyError:
        golink = None

    url = golink.url if golink else ''

    if 'edit' in request.query:
        # Only edit if no suffix after name (e.g. http://go/name?edit)
        return {
            'golink_name': name,
            'golink_url': url,
            'readonly': READONLY,
        }
    elif not golink:
        # Redirect to edit view
        raise web.HTTPSeeOther(url_for_name(request, name).with_query('edit'))
    else:
        raise web.HTTPFound(golink.url)


@aiohttp_jinja2.template('edit.html')
async def get_golink_with_suffix(request: web.Request):
    """Handle GET requests with a suffix."""
    name = request.match_info['name']
    suffix = request.match_info['suffix']

    try:
        golink = request.app['DATABASE'].find_golink_by_name(name)
    except KeyError:
        # Redirect to edit view
        raise web.HTTPSeeOther(url_for_name(request, name).with_query('edit'))

    raise web.HTTPFound(golink.with_suffix(suffix))


async def post_golink(request: web.Request):
    """
    Handle POST requests.
    """
    if READONLY:
        raise web.HTTPForbidden()

    name = request.match_info['name'].strip()
    post = await request.post()

    missing = [key for key in ('url', ) if key not in post]
    if missing:
        raise web.HTTPBadRequest(text='Missing required field: {}'.format(' '.join(missing)))

    url = post['url'].strip()

    try:
        golink = Golink(name, url)
    except ValueError as e:
        raise web.HTTPBadRequest(text='Invalid Golink: {}'.format(e))
    request.app['DATABASE'].insert_or_replace_golink(golink)

    # Redirect to edit view
    raise web.HTTPSeeOther(url_for_name(request, name).with_query('edit'))


async def not_found(request: web.Request):
    raise web.HTTPNotFound()


async def get_robots_txt(request: web.Request):
    # Disallow all robots
    return web.Response(text='User-agent: *\nDisallow: /\n', content_type='text/plain')


def url_for_name(request: web.Request, name) -> yarl.URL:
    return request.app.router['golink'].url_for(name=name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', default='localhost')
    parser.add_argument('-P', '--port', type=int, default=8080)
    parser.add_argument('--database', default=':memory:')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if not READONLY:
        logging.warning('Running in read/write mode. Public edits allowed.')

    app = web.Application()
    app['DATABASE'] = Database.connect(args.database)
    aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader('golink', 'templates'))
    app.router.add_routes([
        web.get('/', get_index, name='index'),
        web.post('/', post_index),
        web.get('/favicon.ico', not_found),
        web.get('/robots.txt', get_robots_txt),
        web.get('/{{name:{0}}}'.format(NAME_RE.pattern), get_golink, name='golink'),
        web.get('/{{name:{0}}}/{{suffix:[^{{}}]*}}'.format(NAME_RE.pattern), get_golink_with_suffix, name='golink_with_suffix'),
        web.post('/{{name:{0}}}'.format(NAME_RE.pattern), post_golink),
    ])
    web.run_app(app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
