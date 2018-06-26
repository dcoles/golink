# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt
import argparse
import logging

from aiohttp import web
import aiohttp_jinja2
import jinja2

from golink import views
from golink.persistence import Database


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', default='localhost')
    parser.add_argument('-P', '--port', type=int, default=8080)
    parser.add_argument('--database', default=':memory:')
    # Don't set to unless in a trusted environment
    parser.add_argument('--noreadonly', action='store_false', dest='readonly', default=True)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    app = web.Application()
    app['DATABASE'] = Database.connect(args.database)
    app['READONLY'] = args.readonly
    aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader('golink', 'templates'))
    app.router.add_routes(views.routes)

    if not app['READONLY']:
        logging.warning('Running in read/write mode. Public edits allowed.')

    web.run_app(app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
