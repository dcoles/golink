# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt
import asyncio
import typing
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import attr
import sqlite3

from golink.model import Golink

CREATE_TABLE_SQL = '''CREATE TABLE IF NOT EXISTS Golinks (
  name VARCHAR PRIMARY KEY COLLATE NOCASE,
  url VARCHAR NOT NULL,
  owner VARCHAR,
  visits INT DEFAULT 0)
'''
FIND_BY_OWNER_SQL = 'SELECT * FROM Golinks WHERE owner=:owner ORDER BY name'
FIND_BY_NAME_SQL = 'SELECT * FROM Golinks WHERE name=:name'
SEARCH_SQL = '''SELECT *
FROM Golinks
WHERE name GLOB :name_glob OR url GLOB :url_glob
ORDER BY visits DESC
LIMIT :limit
'''
INSERT_OR_REPLACE_SQL = 'INSERT OR REPLACE INTO Golinks VALUES(?, ?, ?, ?)'
INCREMENT_SQL = 'UPDATE Golinks SET visits = visits + 1 WHERE name=:name'
DELETE_SQL = 'DELETE FROM Golinks WHERE name=:name'


def _loop_run_in_executor(func):
    def _run(self, *args, **kwargs):
        return self._loop.run_in_executor(
            self._executor, partial(func, self, *args, **kwargs))
    return _run


class Database:
    @classmethod
    def connect(cls, database, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(1)
        con = executor.submit(sqlite3.connect, database).result()
        executor.submit(con.execute, CREATE_TABLE_SQL).result()
        return cls(con, executor, loop)

    def __init__(self, con, executor, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self._con = con
        self._executor = executor
        self._loop = loop

    @_loop_run_in_executor
    def find_by_owner(self, owner) -> typing.Iterator[Golink]:
        return (Golink(*row) for row in self._con.execute(FIND_BY_OWNER_SQL, dict(owner=owner)).fetchall())

    @_loop_run_in_executor
    def find_by_name(self, name):
        value = self._con.execute(FIND_BY_NAME_SQL, dict(name=name)).fetchone()
        if value is None:
            raise KeyError(name)
        return Golink(*value)

    @_loop_run_in_executor
    def search(self, name_or_url, limit=1000):
        name_glob = '*{}*'.format(name_or_url)  # Partial match
        url_glob = '{}*'.format(name_or_url)  # Prefix match
        return (Golink(*row) for row in self._con.execute(SEARCH_SQL, dict(name_glob=name_glob, url_glob=url_glob, limit=limit)).fetchall())

    @_loop_run_in_executor
    def insert_or_replace(self, golink):
        if not isinstance(golink, Golink):
            raise TypeError('Golink required')

        with self._con:
            self._con.execute(INSERT_OR_REPLACE_SQL, attr.astuple(golink))

    @_loop_run_in_executor
    def increment_visits(self, name):
        with self._con:
            self._con.execute(INCREMENT_SQL, dict(name=name))

    @_loop_run_in_executor
    def delete(self, name):
        with self._con:
            self._con.execute(DELETE_SQL, dict(name=name))
