"""
Streamy Server Implementation
"""
from fastapi import FastAPI

from .backend import Backend

#** Variables **#
__all__ = ['webapp', 'Context']

#: fastapi app instance
webapp = FastAPI()

#** Classes **#

class Context:
    """global library var container to pass app config settings"""
    backend: Backend = None

#** Init **#

from .track import api as track_api
from .playlist import api as playlist_api

track_api.apply_blueprint(webapp)
playlist_api.apply_blueprint(webapp)
