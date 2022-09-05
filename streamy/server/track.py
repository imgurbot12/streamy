"""
Streamy Server `Track` API
"""
from typing import Dict, List, Any

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from . import Context
from ..utils import BluePrint

#** Variables **#
__all__ = ['api']

api = BluePrint('/api/v1/track/')

TrackInfo = Dict[str, Any]

#** Routes **#

@api.get('/stream/{id}')
def stream(id: str) -> StreamingResponse:
    """
    stream audio contents over the web

    :param id: track-id to retrieve
    :return:   audio stream over http
    """
    mime, stream = Context.backend.stream(id)
    if stream is None:
        raise HTTPException(status_code=400, detail='Invalid Track ID')
    # render streaming function
    def do_stream():
        with stream:
            yield from stream
    return StreamingResponse(do_stream(), media_type=mime)

@api.get('/info/{id}/')
def info(id: str) -> TrackInfo:
    """
    retrieve details for the specifed track-id

    :param id: track-id associated w/ retrieved details
    :return:   json of track details
    """
    return Context.backend.get_track(id)

@api.get('/info/all/')
def info_all(page: int = 1, limit: int = 25) -> List[TrackInfo]:
    """
    retrieve list of all tracks in the database

    :param page:  page number on paginated results
    :param limit: limit on paginated results
    :return:      list of all possible tracks and thier info
    """
    return Context.backend.all_tracks(page, limit)

@api.get('/info/search/{name}')
def info_search(name: str) -> List[TrackInfo]:
    """
    retrieeve list of track-ids associated w/ given search

    :param name: partial search name being looked up
    :return:     json list of track details
    """
    return Context.backend.search_tracks(name)

