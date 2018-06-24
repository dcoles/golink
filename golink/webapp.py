# Golink webapp
# Author: David Coles <coles.david@gmail.com>
import argparse

from aiohttp import web
import aiohttp_jinja2
import jinja2

from golink.model import Golink


DEFAULT_GOLINKS = {
    'drive': 'http://drive.google.com/',
    'pylib': 'https://docs.python.org/3/library/',
    'search': 'https://www.google.com/search?q=',
}
# TODO(dcoles) Remove once proper authentication is added
READONLY = True  # Don't set to false unless in a trusted environment


@aiohttp_jinja2.template('edit.html')
async def get_index(request):
    """
    Handle index requests.
    """
    query = request.query.get('q', '')
    name = query.split('/', 1)[0]
    golink = request.app['GOLINKS'].get(name)

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

    golink = Golink(post['name'], post['url'])
    # TODO(dcoles) Add persistent storage
    request.app['GOLINKS'][golink.name] = golink

    raise web.HTTPFound(request.app.router['index'].url_for().with_query({'q': golink.name}))


async def get_golink(request):
    """
    Handle golink requests.
    """
    name = request.match_info['golink']
    golink = request.app['GOLINKS'].get(name)
    suffix = request.match_info.get('suffix', '')

    if not golink:
        raise web.HTTPFound(request.app.router['index'].url_for().with_query({'q': name}))

    raise web.HTTPFound(golink.with_suffix(suffix))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', default='localhost')
    parser.add_argument('-P', '--port', type=int, default=8080)
    args = parser.parse_args()

    app = web.Application()
    app['GOLINKS'] = {name: Golink(name, url) for name, url in DEFAULT_GOLINKS.items()}
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
