"""
Streamy Server Implementation
"""
from fastapi import FastAPI

from .backend import AudioBackend, VideoBackend

#** Variables **#
__all__ = ['webapp', 'Context']

#: fastapi app instance
webapp = FastAPI()

#** Classes **#

class Context:
    """global library var container to pass app config settings"""
    audio_backend: AudioBackend
    video_backend: VideoBackend

#** Init **#

import os
from .backend.filesystem import FileSystemBackend

HOME = os.environ['HOME']

# configure web app context
backend = FileSystemBackend('./mcache.db', [f'{HOME}/Music', f'{HOME}/Videos'])
Context.audio_backend = backend
Context.video_backend = backend

from .track import api as track_api
from .video import api as video_api
from .playlist import api as playlist_api

track_api.apply_blueprint(webapp)
video_api.apply_blueprint(webapp)
playlist_api.apply_blueprint(webapp)
