# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt

import argparse
import logging

from aiohttp import web
import aiohttp_jinja2
import jinja2

from golink.model import Golink
from golink.persistence import Database


# TODO(dcoles) Remove once proper authentication is added
READONLY = True  # Don't set to false unless in a trusted environment


@aiohttp_jinja2.template('edit.html')
async def get_index(request):
    """
    Handle index requests.
    """
    query = request.query.get('q', '')
    name = query.split('/', 1)[0]
    try:
        golink = request.app['DATABASE'].find_golink_by_name(name)
    except KeyError:
        golink = None

    return {'golink_name': name, 'golink_url': golink.url if golink else '', 'readonly': READONLY}


async def post_index(request):
    """
    Handle index updates.
    """
    if READONLY:
        raise web.HTTPForbidden()

    post = await request.post()
    missing = [key for key in ('name', 'url') if key not in post]
    if missing:
        raise web.HTTPBadRequest(text='Missing required field: {}'.format(' '.join(missing)))

    try:
        golink = Golink(post['name'].strip(), post['url'].strip())
    except ValueError as e:
        raise web.HTTPBadRequest(text='Invalid Golink: {}'.format(e))
    request.app['DATABASE'].insert_or_replace_golink(golink)

    raise web.HTTPFound(request.app.router['index'].url_for().with_query({'q': golink.name}))


async def get_golink(request):
    """
    Handle golink requests.
    """
    name = request.match_info['golink']
    suffix = request.match_info.get('suffix', '')

    try:
        golink = request.app['DATABASE'].find_golink_by_name(name)
    except KeyError:
        golink = None

    if not golink:
        raise web.HTTPFound(request.app.router['index'].url_for().with_query({'q': name}))

    raise web.HTTPFound(golink.with_suffix(suffix))


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
    app.add_routes([
        web.get('/', get_index, name='index'),
        web.post('/', post_index),
        web.get('/{golink}', get_golink),
        web.get('/{golink}/{suffix:[^{}]*}', get_golink),
    ])
    web.run_app(app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
