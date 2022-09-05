"""
Streamy Server `Track` API
"""
from typing import Dict, List

from . import Context
from ..utils import BluePrint

#** Variables **#
__all__ = ['api']

api = BluePrint('/api/v1/track/')

TrackInfo = Dict[str, str]

#** Routes **#

@api.get('/all/')
def all(page: int = 1, limit: int = 25) -> List[TrackInfo]:
    """
    retrieve list of all tracks in the database

    :return: list of all possible tracks and thier info
    """
    return Context.backend.all_tracks(page, limit)

@api.get('/get/{id}/')
def get(id: str) -> TrackInfo:
    """
    retrieve details for the specifed track-id

    :param id: track-id associated w/ retrieved details
    :return:   json of track details
    """
    return Context.backend.get_track(id)

@api.get('/search/{name}')
def search(name: str) -> List[TrackInfo]:
    """
    retrieeve list of track-ids associated w/ given search

    :param name: partial search name being looked up
    :return:     json list of track details
    """
    return Context.backend.search_tracks(name)

