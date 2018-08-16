# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt

from typing import Iterator

from golink.model import Golink


class Database:
    async def find_by_owner(self, owner) -> Iterator[Golink]:
        """Find all Golinks created by `owner`."""
        raise NotImplementedError()

    async def find_by_name(self, name) -> Golink:
        """Find a single Golink by `name`. Raises KeyError if not found."""
        raise NotImplementedError()

    async def search(self, query, limit=1000) -> Iterator[Golink]:
        """Search for Golinks using a `query` string."""
        raise NotImplementedError()

    async def insert_or_replace(self, golink: Golink):
        """Insert or replace a Golink."""
        raise NotImplementedError()

    async def increment_visits(self, name):
        """Increment the number of visits for a Golink by `name`."""
        raise NotImplementedError()

    async def delete(self, name):
        """Delete an existing Golink by `name`."""
        raise NotImplementedError()


