"""
Server Data Backend Implementations
"""
from typing import Tuple, List, Protocol, Optional
from abc import abstractmethod
from dataclasses import dataclass, field

#** Classes **#

@dataclass
class TrackInfo:
    id:     str
    path:   str
    name:   str
    mime:   str
    length: int = 0
    artist: str = ''
    album:  str = ''
    track:  int = 0

@dataclass
class PlayList:
    id:      str
    name:    str
    creator: str       = ''
    tracks:  List[str] = field(default_factory=list)

class FileStream(Protocol):

    @abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, *args):
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError

class Backend(Protocol):
   
    @abstractmethod
    def stream(self, id: str) -> Optional[Tuple[str, FileStream]]:
        raise NotImplementedError

    @abstractmethod
    def all_tracks(self, page: int, limit: int = 10) -> List[TrackInfo]:
        raise NotImplementedError

    @abstractmethod
    def get_track(self, id: str) -> Optional[TrackInfo]:
       raise NotImplementedError

    @abstractmethod
    def search_tracks(self, search: str, limit: int = 25) -> List[TrackInfo]:
        raise NotImplementedError

    @abstractmethod
    def get_playlist(self, id: str) -> Optional[PlayList]:
       raise NotImplementedError

    @abstractmethod
    def search_playlists(self, search: str, limit: int = 25) -> List[PlayList]:
        raise NotImplementedError

