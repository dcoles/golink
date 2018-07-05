# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt

from aiohttp import web

from golink import model


class Auth:
    def __init__(self, request: web.Request):
        self.request = request

    @property
    def readonly(self):
        return self.request.app.get('READONLY', False)

    @property
    def authenticated(self):
        """Is the current user authenticated?"""
        return self.current_user() is not None

    def can_create(self):
        """Can the current user create new Golinks?"""
        # All authenticated users can create new Golinks
        return self.authenticated and not self.readonly

    def can_edit(self, golink: model.Golink):
        """Can the current user edit a specific Golink?"""
        # Only the Golink's owner can edit it
        return self.authenticated and self.current_user() == golink.owner and not self.readonly

    def current_user(self):
        """
        Get the current authenticated user.

        Returns `None` if not authenticated.
        """
        raise NotImplementedError()


class NullAuth(Auth):
    """Authenticator that never authenticates."""
    def current_user(self):
        return None


class AnonymousAuth(Auth):
    """Authenticator that always authenticates as an anonymous user."""

    USER = 'anonymous'

    def current_user(self):
        return self.USER


AUTHENTICATORS = {
    'null': NullAuth,
    'anonymous': AnonymousAuth,
}
