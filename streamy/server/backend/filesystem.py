"""
FileSystem Backend for Streamy Server Implementation
"""
import os
import json
import hashlib
from dbm import gnu as gnudb
from typing import Dict, List, Optional, Iterator
from collections import namedtuple
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor

import ffmpeg

from . import TrackInfo, PlayList, Backend

#** Varaibles **#
__all__ = ['FileSystemBackend']

#: valid and supported music extensions
VALID_EXTENSIONS = {'mp3', }

Record = namedtuple('Record', ('id', 'name', 'filepath'))

#** Functions **#

def generate_id(path: str) -> str:
    """
    generate unique-id for the given music file

    :param path: music track filepath
    """
    sha1 = hashlib.sha1()
    sha1.update(path.encode())
    return sha1.hexdigest()

def scan_track(record: Record) -> TrackInfo:
    """
    scan the given music file for track metadata

    :param record: internal system record object
    :return:       generated `TrackInfo` object
    """
    print(f'scanning {record.name!r}')
    audio    = ffmpeg.probe(record.filepath)
    format   = audio['format']
    tags     = audio['format']['tags'] 
    duration = float(format['duration'])
    return TrackInfo(
        id=record.id,
        path=record.filepath,
        name=tags.get('title') or record.name,
        length=int(duration),
        album=tags.get('album'),
        artist=tags.get('artist'),
        track=tags.get('track'),
    )

def scan_tracks(records: List[Record], threads: int = 5) -> List[TrackInfo]:
    """
    scan a list of records as fast as possible using threads

    :param records: list of basic music record objects to scan
    :param threads: max number of threads allowed
    :return:        list of more in-depth trackinfo objects
    """
    with ThreadPoolExecutor(max_workers=threads) as pool:
        return pool.map(scan_track, records) 

#** Classes **#

class DbmCache:
    TRACK_PREFIX = 't_'

    def __init__(self, cache: str):
        self.cache = gnudb.open(cache, 'cf')

    def __del__(self):
        self.cache.close()
    
    def flush(self):
        self.cache.sync()
    
    def iter_keys(self) -> Iterator:
        """
        iterate any and all fields in database
        """
        key = self.cache.firstkey()
        while key is not None:
            yield key.decode()
            key = self.cache.nextkey(key)
    
    def iter_tracks(self, page: int = 1, limit: int = 0) -> Iterator:
        """
        iterate all tracks stored in database
        """
        start  = ( page - 1 ) * limit
        end    = page * limit
        prefix = self.TRACK_PREFIX
        tracks = (k for k in self.iter_keys() if k.startswith(prefix))
        for n, key in enumerate(tracks, 0):
            if limit > 0:
                if n < start:
                    continue
                if n >= end:
                    break
            yield TrackInfo(**json.loads(self.cache[key].decode()))

    def get_track(self, id: str) -> Optional[TrackInfo]:
        """
        retrieve track from dbm-cache

        :param id: track-id being retrieved
        :return:   track-info object if id existed in cache
        """
        info = self.cache.get(f'{self.TRACK_PREFIX}{id}', None)
        if info is not None:
            return TrackInfo(**json.loads(info.decode()))

    def set_track(self, info: TrackInfo):
        """
        store `TrackInfo` object in dbm-cache

        :param info: track-info object being stored
        """
        value = json.dumps(asdict(info)).encode()
        self.cache[f'{self.TRACK_PREFIX}{info.id}'] = value
 
@dataclass
class FileSystemBackend(Backend):
    cache:     str
    paths:     List[str]
    music:     Dict[str, Record] = field(repr=False, default_factory=dict)
    skip_walk: bool              = False
    
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
        queue = []
        for root, _, files in os.walk(path, topdown=False):
            for name in files:
                # skip over invalid/unsupported filetypes
                if not any(name.endswith(ext) for ext in VALID_EXTENSIONS):
                    continue
                fpath  = os.path.join(root, name)
                id     = generate_id(fpath)
                record = Record(id, name, fpath)
                # attempt to retrieve track-info record
                info = self.db.get_track(id)
                if info is not None:
                    self.music[id] = info
                    continue
                # add to thread-pool queue to scan
                queue.append(record)
        # complete db cache and load track-info into memory by scanning queue
        for info in scan_tracks(queue):
            self.music[info.id] = info
            self.db.set_track(info)
        # only update db if there were new tracks scanned
        if queue:
            print('flushing db')
            self.db.flush()


    def all_tracks(self, page: int = 1, limit: int = 10) -> List[TrackInfo]:
        """
        retrieve all tracks w/ a pagination control

        :param page:  pagination page number
        :param limit: limit number of results
        :return:      paginated tracklist
        """
        return list(self.db.iter_tracks(page, limit))

    def get_track(self, id: str) -> Optional[TrackInfo]:
        """
        retrieve track from the given id

        :param id: track-id
        """
        return self.music.get(id)

    def search_tracks(self, search: str, limit: int = 25) -> List[TrackInfo]:
        """
        search for related tracks to the given search

        :param search: search terms for track
        :param limit:  limit the number of results
        :return:       list of tracks that match the given search
        """
        search, results = search.lower(), []
        for record in self.music.values():
            terms = (record.name, record.artist, record.album)
            items = (t.lower() for t in terms if t)
            if any(search in term for term in items):
                results.append(record)
            if limit > 0 and len(results) >= limit:
                break
        return results

    def get_playlist(self, id: str) -> Optional[PlayList]:
        pass

    def search_playlists(self, search: str, limit: int = 25) -> List[PlayList]:
        return []
