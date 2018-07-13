# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt

import typing

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


class Database:
    @classmethod
    def connect(cls, database):
        con = sqlite3.connect(database)
        con.execute(CREATE_TABLE_SQL)
        return cls(con)

    def __init__(self, con):
        self._con = con

    def find_by_owner(self, owner) -> typing.Iterator[Golink]:
        for row in self._con.execute(FIND_BY_OWNER_SQL, dict(owner=owner)):
            yield Golink(*row)

    def find_by_name(self, name):
        value = self._con.execute(FIND_BY_NAME_SQL, dict(name=name)).fetchone()
        if value is None:
            raise KeyError(name)
        return Golink(*value)

    def search(self, name_or_url, limit=1000):
        name_glob = '*{}*'.format(name_or_url)  # Partial match
        url_glob = '{}*'.format(name_or_url)  # Prefix match
        for row in self._con.execute(SEARCH_SQL, dict(name_glob=name_glob, url_glob=url_glob, limit=limit)):
            yield Golink(*row)

    def insert_or_replace(self, golink):
        if not isinstance(golink, Golink):
            raise TypeError('Golink required')

        with self._con:
            self._con.execute(INSERT_OR_REPLACE_SQL, attr.astuple(golink))

    def increment_visit(self, golink):
        if not isinstance(golink, Golink):
            raise TypeError('Golink required')

        with self._con:
            self._con.execute(INCREMENT_SQL, dict(name=golink.name))
