"""gunicorn WSGI server configuration."""
from __future__ import unicode_literals
import multiprocessing
import gunicorn.app.base
from gunicorn.six import iteritems

forwarded_allow_ips = '*'
secure_scheme_headers = {'X-FORWARDED-PROTO': 'https',}


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1