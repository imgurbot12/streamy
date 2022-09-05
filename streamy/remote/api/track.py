"""
Streamy Remote `Track` REST API
"""
from typing import Dict, Any

from ...utils import BluePrint

#** Variables **#

api = BluePrint('/api/v1/action/')

TrackInfo = Dict[str, Any]

#** Routes **#

@api.get('/art/')
def cover_art():
    pass

@api.get('/info/')
def info() -> TrackInfo:
    pass

@api.get('/time/')
def time_get() -> int:
    pass

@api.put('/time/{time}')
def time_set(time: int):
    pass

@api.get('/sink/')
def audio_sink():
    pass
