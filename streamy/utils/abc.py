"""
Common DataTypes between `Server` and `Remote` Implementations
"""
from typing import Optional, TypeVar, Generic, List
from typing_extensions import Annotated

from pyderive.extensions.validate import *

#** Variables **#
__all__ = ['MediaMeta', 'AudioMeta', 'VideoMeta', 'PagedList']

#: basic generic typevar
T = TypeVar('T')

#: object-id validator
ObjectId = Annotated[str, Regex(r'^\w+$')]

#** Classes **#

class MediaMeta(BaseModel, compat=True):
    id:       ObjectId
    name:     str
    mime:     str
    duration: float

class AudioMeta(MediaMeta):
    album:    Optional[str] = None
    artist:   Optional[str] = None
    track:    Optional[str] = None

class VideoMeta(MediaMeta):
    comment: Optional[str] = None

class PagedList(BaseModel, Generic[T], compat=True):
    items: List[T]
    size:  int
    page:  int
    pages: Optional[int] = None
