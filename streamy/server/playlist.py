"""
Streamy Server `Playlist` API
"""
from typing import Dict, List

from ..utils import BluePrint

#** Variables **#
__all__ = ['api']

api = BluePrint('/api/v1/playlist/')

PlayList = Dict[str, str]

#** Routes **#

@api.put('/new/')
def new():
    """
    generate a new playlist in system
    """
    pass

@api.get('/get/{id}/')
def get(id: str) -> PlayList:
    """
    retrieve playlist info using the given id

    :param id: playlist id
    :return:   playlist info
    """
    return {'tracks': 0, 'name': 'Test Playlist'}

@api.get('/search/{name}/')
def search(name: str) -> List[PlayList]:
    """
    retrieve list of playlists associated w/ the given name

    :param name: partial search name for playlists
    :return:     list of playlist objects
    """
    return []
