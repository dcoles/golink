# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt

import re
from typing import Iterator

import attr
import pymongo
import pymongo.database

from golink import persistence
from golink.model import Golink

_GOLINK_PROJECTION = {field.name: True for field in attr.fields(Golink)}
_GOLINK_PROJECTION['_id'] = False  # Don't include "_id" field


class Database(persistence.Database):
    @classmethod
    def connect(cls, url):
        client = pymongo.MongoClient(url)
        return cls(client)

    @property
    def _db(self) -> pymongo.database.Database:
        return self.client.golink

    @property
    def _golinks(self) -> pymongo.collection.Collection:
        return self._db['golinks']

    def __init__(self, client: pymongo.MongoClient):
        self.client = client

    async def find_by_owner(self, owner) -> Iterator[Golink]:
        return self._find_golinks({'owner': owner})

    def _find_golinks(self, filter, limit=0):
        return (Golink(**obj) for obj in self._golinks.find(filter, projection=_GOLINK_PROJECTION, limit=limit))

    async def find_by_name(self, name) -> Golink:
        obj = self._golinks.find_one({'name': name}, projection=_GOLINK_PROJECTION)
        if not obj:
            raise KeyError(name)

        return Golink(**obj)

    async def search(self, query, limit=1000) -> Iterator[Golink]:
        name_re = re.escape(query)  # Partial match
        return self._find_golinks({'name': {'$regex': name_re}}, limit=limit)

    async def insert_or_replace(self, golink: Golink):
        self._golinks.replace_one({'name': golink.name}, attr.asdict(golink), upsert=True)

    async def increment_visits(self, name):
        self._golinks.update_one({'name': name}, {'$inc': {'visits': 1}})

    async def delete(self, name):
        self._golinks.delete_one({'name': name})
