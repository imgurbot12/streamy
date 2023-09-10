"""
FileSystem Backend for Streamy Server Implementation
"""
import os
import socket
import hashlib
from dbm import gnu as gnudb
from typing import Dict, List, Optional, Iterator, NamedTuple, Set, Type, TypeVar
from concurrent.futures import ThreadPoolExecutor

import ffmpeg
from pyderive import dataclass, field

from . import BaseInfo, AudioInfo, AudioStream, AudioBackend, UserSearch
from . import VideoInfo, VideoStream,  VideoBackend
from ...utils import AudioMeta, VideoMeta

#** Varaibles **#
__all__ = ['FileSystemBackend']

#: typevar of serde type
S = TypeVar('S', bound=BaseInfo)

#: category matches hostname
CATEGORIES = {socket.gethostname(), }

#: valid and supported music extensions
VALID_AUDIO_EXTENSIONS = {'mp3', }

#: valid and supported video extensions
VALID_VIDEO_EXTENSIONS = {'mp4', }

class Record(NamedTuple):
    id:       str
    name:     str
    filepath: str

#** Functions **#

def generate_id(path: str) -> str:
    """
    generate unique-id for the given music file

    :param path: music track filepath
    :return:     generated unique-id for the given path
    """
    sha1 = hashlib.sha1()
    sha1.update(path.encode())
    return sha1.hexdigest()

def scan_track(record: Record) -> AudioInfo:
    """
    scan the given music file for track metadata

    :param record: internal system record object
    :return:       generated `TrackInfo` object
    """
    print(f'scanning {record.name!r}')
    audio    = ffmpeg.probe(record.filepath)
    format   = audio['format']
    tags     = audio['format']['tags'] 
    return AudioInfo(
        id=record.id,
        path=record.filepath,
        size=int(format['size']),
        bitrate=int(format['bit_rate']),
        meta=AudioMeta(
            id=record.id,
            name=tags.get('title') or record.name,
            mime=f'audio/{format.get("format_name", "unknown")}',
            album=tags.get('album'),
            artist=tags.get('artist'),
            track=tags.get('track'),
            duration=float(format['duration']),
        )
    )

def scan_video(record: Record) -> VideoInfo:
    """
    scan the given video file for video metadata

    :param record: internal system record object
    :return:       generated `VideoInfo` object
    """
    print(f'scanning {record.name!r}')
    video  = ffmpeg.probe(record.filepath)
    format = video['format']
    tags   = video['format']['tags']
    return VideoInfo(
        id=record.id,
        path=record.filepath,
        size=int(format['size']),
        bitrate=int(format['bit_rate']),
        meta=VideoMeta(
            id=record.id,
            name=tags.get('title') or record.name,
            mime=f'video/{format.get("format_name", "unkown")}',
            comment=tags.get('comment', None),
            duration=float(format['duration']),
        )
    )

def scan_tracks(records: List[Record], threads: int = 5) -> Iterator[AudioInfo]:
    """
    scan a list of records as fast as possible using threads

    :param records: list of basic music record objects to scan
    :param threads: max number of threads allowed
    :return:        list of more in-depth trackinfo objects
    """
    with ThreadPoolExecutor(max_workers=threads) as pool:
        return pool.map(scan_track, records) 

def scan_videos(records: List[Record], threads: int = 5) -> Iterator[VideoInfo]:
    """
    scan a list of records as fast as possible using threads

    :param records: list of basic music record objects to scan
    :param threads: max number of threads allowed
    :return:        list of more in-depth videoinfo objects
    """
    with ThreadPoolExecutor(max_workers=threads) as pool:
        return pool.map(scan_video, records) 

#** Classes **#

class DbmCache:
    TRACK_PREFIX = 't_'
    VIDEO_PREFIX = 'v_'

    def __init__(self, cache: str):
        self.cache = gnudb.open(cache, 'cf')

    def __del__(self):
        self.cache.close()
 
    def flush(self):
        self.cache.sync()

    def iter_keys(self) -> Iterator[str]:
        """
        iterate any and all fields in database
        """
        key = self.cache.firstkey()
        while key is not None:
            yield key.decode()
            key = self.cache.nextkey(key)

    def _iter(self, page: int, size: int, prefix: str, item: Type[S]) -> Iterator[S]:
        """
        iterate all items of a particular type and retrieve results
        """
        start  = ( page - 1 ) * size
        end    = page * size
        items  = (k for k in self.iter_keys() if k.startswith(prefix))
        for n, key in enumerate(items, 0):
            if size > 0:
                if n < start:
                    continue
                if n >= end:
                    break
            yield item.from_json(self.cache[key])

    def _get(self, id: str, prefix: str, item: Type[S]) -> Optional[S]:
        """
        retrieve item of the given type associated w/ the given id
        """
        info = self.cache.get(f'{prefix}{id}', None)
        if info is not None:
            return item.from_json(info)
 
    def _set(self, prefix: str, item: BaseInfo):
        """
        set new item into db using the given prefix and data-object 
        """
        key = f'{prefix}{item.id}'
        self.cache[key] = item.to_json()

    def iter_tracks(self, page: int = 1, size: int = 0) -> Iterator[AudioInfo]:
        """
        iterate all tracks stored in database

        :param page: page of items to retrieve
        :param size: page size for returned items
        :return:     iterator collecting paged audio tracks
        """
        return self._iter(page, size, self.TRACK_PREFIX, AudioInfo)

    def get_track(self, id: str) -> Optional[AudioInfo]:
        """
        retrieve track from dbm-cache

        :param id: track-id being retrieved
        :return:   track-info object if id existed in cache
        """
        return self._get(id, self.TRACK_PREFIX, AudioInfo) 

    def set_track(self, info: AudioInfo):
        """
        store `AudioInfo` object in dbm-cache

        :param info: track-info object being stored
        """
        self._set(self.TRACK_PREFIX, info) 

    def iter_videos(self, page: int = 1, limit: int = 0) -> Iterator[VideoInfo]:
        """
        iterate all videos stored in database
        """
        return self._iter(page, limit, self.VIDEO_PREFIX, VideoInfo)

    def get_video(self, id: str) -> Optional[VideoInfo]:
        """
        retrieve video from dbm-cache

        :param id: video-id being retrieved
        :return:   video-info object if id existed in cache
        """
        return self._get(id, self.VIDEO_PREFIX, VideoInfo) 

    def set_video(self, info: VideoInfo):
        """
        store `VideoInfo` object in dbm-cache

        :param info: track-info object being stored
        """
        self._set(self.VIDEO_PREFIX, info) 

#TODO: implement playlist-backend for system

@dataclass
class FileSystemBackend(AudioBackend, VideoBackend):
    cache:     str
    paths:     List[str]
    music:     Dict[str, AudioInfo] = field(repr=False, default_factory=dict)
    video:     Dict[str, VideoInfo] = field(repr=False, default_factory=dict)
    skip_walk: bool                 = False

    def __post_init__(self):
        self.db = DbmCache(self.cache)
        if not self.skip_walk:
            for path in self.paths:
                self.scan_path(path)
        else:
            self.load_cache()

    def load_cache(self):
        """
        instead of scanning filesystem just load items from dbm-cache
        """
        for track in self.db.iter_tracks():
            self.music[track.id] = track

    def scan_path(self, path: str):
        """
        scan the given path location and cache tracks listed
        
        :param path: directory path to scan
        """
        audio_queue = []
        video_queue = []
        for root, _, files in os.walk(path, topdown=False):
            for name in files:
                # skip over invalid/unsupported filetypes
                if any(name.endswith(ext) for ext in VALID_AUDIO_EXTENSIONS):
                    ftype = 'audio'
                elif any(name.endswith(ext) for ext in VALID_VIDEO_EXTENSIONS):
                    ftype = 'video'
                else:
                    continue
                fpath  = os.path.join(root, name)
                id     = generate_id(fpath)
                record = Record(id, name, fpath)
                # attempt to retrieve track-info record
                if ftype == 'audio':
                    info = self.db.get_track(id)
                    if info is not None:
                        self.music[id] = info
                        continue
                    audio_queue.append(record)
                else:
                    info = self.db.get_video(id)
                    if info is not None:
                        self.video[id] = info
                        continue
                    video_queue.append(record)
        # complete db cache and load track-info into memory by scanning queue
        for info in scan_tracks(audio_queue):
            self.music[info.id] = info
            self.db.set_track(info)
        for info in scan_videos(video_queue):
            self.video[info.id] = info
            self.db.set_video(info)
        # only update db if there were new tracks scanned
        if audio_queue or video_queue:
            print('flushing db')
            self.db.flush()
    
    ## Audio Backend
    
    def get_categories(self) -> Set[str]:
        """
        retrieve categories for audio and video

        :return: categories associated w/ backend
        """
        return CATEGORIES

    def stream_track(self, id: str) -> Optional[AudioStream]:
        """
        return filestream for the given track-id

        :param id: track-id being retrievd
        :return:   filestream if id is valid
        """
        info = self.get_track(id)
        if info is not None:
            return AudioStream(info, open(info.path, 'rb'))

    def all_tracks(self, page: int = 1, limit: int = 10) -> List[AudioInfo]:
        """
        retrieve all tracks w/ a pagination control

        :param page:  pagination page number
        :param limit: limit number of results
        :return:      paginated tracklist
        """
        return list(self.db.iter_tracks(page, limit))

    def get_track(self, id: str) -> Optional[AudioInfo]:
        """
        retrieve track from the given id

        :param id: track-id
        """
        return self.music.get(id)

    def search_tracks(self, search: UserSearch) -> List[AudioInfo]:
        """
        search for related tracks to the given search

        :param search: search terms for track
        :param limit:  limit the number of results
        :return:       list of tracks that match the given search
        """
        if not search.match_categories(self.get_categories()):
            return []
        tags, results = search.tags(), []
        for track in self.music.values():
            terms = (track.meta.name, track.meta.artist, track.meta.album)
            items = (t.lower() for t in terms if t)
            if all(any(tag in term for term in items) for tag in tags):
                results.append(track)
            if search.limit > 0 and len(results) >= search.limit:
                break
        return results

    ## Video Backend

    def stream_video(self, id: str) -> Optional[VideoStream]:
        """
        return filestream for the given video-id

        :param id: video-id being retrievd
        :return:   filestream if id is valid
        """
        info = self.get_video(id)
        if info is not None:
            return VideoStream(info, open(info.path, 'rb'))

    def all_videos(self, page: int = 1, limit: int = 10) -> List[VideoInfo]:
        """
        retrieve all videos w/ a pagination control

        :param page:  pagination page number
        :param limit: limit number of results
        :return:      paginated tracklist
        """
        return list(self.db.iter_videos(page, limit))

    def get_video(self, id: str) -> Optional[VideoInfo]:
        """
        retrieve video from the given id

        :param id: video-id
        """
        return self.video.get(id)

    def search_videos(self, search: UserSearch) -> List[VideoInfo]:
        """
        search for related tracks to the given search

        :param search: search terms for track
        :param limit:  limit the number of results
        :return:       list of videos that match the given search
        """
        if not search.match_categories(self.get_categories()):
            return []
        tags, results = search.tags(), []
        for track in self.video.values():
            terms = (track.meta.name, track.meta.comment)
            items = (t.lower() for t in terms if t)
            if all(any(tag in term for term in items) for tag in tags):
                results.append(track)
            if search.limit > 0 and len(results) >= search.limit:
                break
        return results
