"""
Server Data Backend Implementations
"""
from typing import *
from typing import BinaryIO
from abc import abstractmethod

from pyderive import field
from pyderive.extensions.serde import Serde
from pyderive.extensions.validate import *

from ...utils import AudioMeta, VideoMeta

T = TypeVar('T')
I = TypeVar('I', bound='BaseInfo')

#** Classes **#

class BaseInfo(BaseModel, Serde, Generic[T], compat=True):
    id:      str
    path:    str    
    meta:    T
    size:    int = 0
    bitrate: int = 0

class BaseStream(BaseTuple, Generic[I]):
    info:   I
    stream: Union[URL, BinaryIO]

class AudioInfo(BaseInfo[AudioMeta]):
    pass

class AudioStream(BaseStream[AudioInfo]):
    pass 

class VideoInfo(BaseInfo[VideoMeta]):
    pass

class VideoStream(BaseStream[VideoInfo]):
    pass

class PlayList(BaseModel, compat=True):
    id:      str
    name:    str
    creator: str       = ''
    tracks:  List[str] = field(default_factory=list)

class UserSearch(BaseModel, compat=True):
    q:        str
    limit:    int           = 25
    category: Optional[str] = None

    def tags(self) -> Set[str]:
        return {t.lower() for t in self.q.split()}

    def match_categories(self, categories: Set[str]) -> bool:
        if self.category is None:
            return True
        overlap = {c for c in self.category.split()} & categories
        return len(overlap) > 0

class AudioBackend(Protocol):
    
    @abstractmethod
    def get_categories(self) -> Set[str]:
        raise NotImplementedError

    @abstractmethod
    def stream_track(self, id: str) -> Optional[AudioStream]:
        raise NotImplementedError

    @abstractmethod
    def all_tracks(self, page: int, size: int) -> List[AudioInfo]:
        raise NotImplementedError

    @abstractmethod
    def get_track(self, id: str) -> Optional[AudioInfo]:
       raise NotImplementedError

    @abstractmethod
    def search_tracks(self, search: UserSearch) -> List[AudioInfo]:
        raise NotImplementedError

class VideoBackend(Protocol):

    @abstractmethod
    def get_categories(self) -> Set[str]:
        raise NotImplementedError

    @abstractmethod
    def stream_video(self, id: str) -> Optional[VideoStream]:
        raise NotImplementedError

    @abstractmethod
    def all_videos(self, page: int, size: int) -> List[VideoInfo]:
        raise NotImplementedError

    @abstractmethod
    def get_video(self, id: str) -> Optional[VideoInfo]:
       raise NotImplementedError

    @abstractmethod
    def search_videos(self, search: UserSearch) -> List[VideoInfo]:
        raise NotImplementedError

class PlaylistBackend(Protocol):

    @abstractmethod
    def get_playlist(self, id: str) -> Optional[PlayList]:
       raise NotImplementedError

    @abstractmethod
    def search_playlists(self, search: str, limit: int = 25) -> List[PlayList]:
        raise NotImplementedError

