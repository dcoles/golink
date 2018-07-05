# Copyright 2018 David Coles <coles.david@gmail.com>
# This project is licensed under the terms of the MIT license. See LICENSE.txt

import re
from urllib.parse import urlsplit, urlunsplit

import attr

NAME_RE = re.compile(r'[0-9a-zA-Z._-]+')
VALID_SCHEMES = {'http', 'https'}


def validate_name(name):
    """Validate a Golink name."""
    if not name:
        raise ValueError('Name is required')

    if not NAME_RE.fullmatch(name):
        raise ValueError('Name must match {}'.format(NAME_RE.pattern))


def validate_url(url):
    """Validate a Golink URL."""
    if not url:
        raise ValueError('URL is required')

    split = urlsplit(url)
    if split.scheme not in VALID_SCHEMES:
        raise ValueError('URL scheme must be one of {!r}'.format(VALID_SCHEMES))
    if not split.netloc:
        raise ValueError('URL must contain a hostname')


@attr.s
class Golink:
    """A Golink."""
    name = attr.ib(validator=lambda _, __, v: validate_name(v))
    url = attr.ib(validator=lambda _, __, v: validate_url(v))
    owner = attr.ib(default=None)

    def with_suffix(self, suffix=''):
        base_url = urlsplit(self.url, allow_fragments=False)
        # Append suffix to the base URL path (or anything following it)
        path = urlunsplit(('', '', base_url.path, base_url.query, '')) + suffix
        # Join everything back together again, ensuring scheme and netloc are unmodified
        return urlunsplit((base_url.scheme, base_url.netloc, path, '', ''))
