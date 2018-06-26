# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt
import typing

import attr
import sqlite3

from golink.model import Golink


class Database:
    @classmethod
    def connect(cls, database):
        con = sqlite3.connect(database)
        con.execute('CREATE TABLE IF NOT EXISTS Golinks (name STRING PRIMARY KEY, url STRING)')
        return cls(con)

    def __init__(self, con):
        self.con_ = con

    def golinks(self) -> typing.Iterator[Golink]:
        for row in self.con_.execute('SELECT name, url FROM Golinks ORDER BY name'):
            yield Golink(*row)

    def find_golink_by_name(self, name):
        value = self.con_.execute('SELECT name, url FROM Golinks WHERE name == ?', (name,)).fetchone()
        if value is None:
            raise KeyError(name)
        return Golink(*value)

    def insert_or_replace_golink(self, golink):
        if not isinstance(golink, Golink):
            raise TypeError('Golink required')

        with self.con_:
            self.con_.execute('INSERT OR REPLACE INTO Golinks VALUES(?, ?)', attr.astuple(golink))
