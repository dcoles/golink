# Golink webapp
# Author: David Coles <coles.david@gmail.com>
import argparse

import attr
from aiohttp import web
import aiohttp_jinja2
import jinja2


DEFAULT_GOLINKS = {
    'drive': 'http://drive.google.com/',
    'pylib': 'https://docs.python.org/3/library/',
    'search': 'https://www.google.com/search?q=',
}
UNSAFE = False  # Don't enable unless in a trusted environment


@attr.s
class Golink:
    """
    A golink.
    """
    name = attr.ib()
    url = attr.ib()



@aiohttp_jinja2.template('index.html')
async def get_index(request):
    """
    Handle index requests.
    """
    query = request.query.get('q', '')
    name = query.split('/', 1)[0]
    golink = request.app['GOLINKS'].get(name)
    if not golink:
        return {'golink': {'name': name}}

    return {'golink': attr.asdict(golink)}


async def post_index(request):
    """
    Handle index updates.
    """
    # TODO(dcoles) Remove once proper authentication is added
    if not UNSAFE:
        # Don't allow modification
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
    extra = request.match_info.get('extra', '')

    if not golink:
        raise web.HTTPFound(request.app.router['index'].url_for().with_query({'q': name}))

    url = golink.url + extra
    raise web.HTTPFound(url)


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
        web.get('/{golink}/{extra:[^{}]*}', get_golink),
    ])
    web.run_app(app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
