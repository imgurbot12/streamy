from os import environ
from typing import List
from urllib.parse import urlparse, parse_qs

import cli
import uvicorn

from . import Context, webapp
from .backend import AudioBackend
from .backend.filesystem import FileSystemBackend

#** Variables **#

#: retrieve home folder
HOME = environ['HOME']

#** Functions **#

def apply_kwargs(key: str, query: dict, kwargs: dict):
    """
    conditionally transfer kwargs value to query kwargs
    """
    if key in kwargs and key not in query:
        query[key] = kwargs[key]

def get_backend(ctx: cli.Context, uri: str, **kwargs):
    """
    parse the given db-uri into a valid backend object

    :param uri: db-uri
    """
    url  = urlparse(uri)
    if url.scheme == 'file':
        path  = url.netloc or url.path
        query = parse_qs(url.query)
        apply_kwargs('paths', query, kwargs)
        return FileSystemBackend(path, **query)
    ctx.on_usage_error(f'invalid uri scheme: {url.scheme!r}')

#** Commands **#

@cli.app()
async def server(ctx: cli.Context):
    """
    spawn and operate a `Streamy` server instance

    :param ctx:    cli context object
    """
    # configure web app context
    backend = FileSystemBackend('./mcache.db', [f'{HOME}/Music', f'{HOME}/Videos'])
    Context.audio_backend = backend
    Context.video_backend = backend
    # run web service
    config = uvicorn.Config(app=webapp)
    server = uvicorn.Server(config=config)
    await server.serve()

#** Init **#

if __name__ == '__main__':
    server.run()
