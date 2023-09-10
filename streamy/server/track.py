"""
Streamy Server `Track` API
"""
from typing import *
from typing import BinaryIO

from fastapi import Depends, Header, HTTPException, Query
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse

from . import Context
from .backend import BaseStream, UserSearch
from ..utils import AudioMeta, PagedList, BluePrint

#** Variables **#
__all__ = ['api']

api = BluePrint('/api/v1/track/')

class PagedAudio(PagedList[AudioMeta]):
    pass

#** Functions **#

def parse_range_header(header: str, file_size: int) -> Tuple[int, int]:
    """
    parse and evaluate the given range-header to get valid start/end indexes

    :param header:    header raw value
    :param file_size: file-size of stream (max end value)
    :return:          (start / end) range index
    """
    try:
        h     = header.split('=', 1)[-1].split("-")
        start = int(h[0]) if h[0] != "" else 0
        end   = int(h[1]) if h[1] != "" else file_size - 1
        if start > end or start < 0 or end > file_size - 1:
            raise ValueError('invalid range')
    except ValueError:
        raise HTTPException(416, detail=f'Invalid Range: {header!r})')
    return start, end

def read_chunked_range(f: BinaryIO, start: int, end: int, chunk_size: int):
    """
    read a the specified file w/ given start/end range and max chunk size

    :param f:          file being read
    :param start:      starting byte index
    :param end:        ending byte index
    :param chunk_size: maxiumum allowed chunk read size
    """
    with f:
        f.seek(start)
        while (pos := f.tell()) <= end:
            read_size = min(chunk_size, end + 1 - pos)
            yield f.read(read_size)

def streaming_response(stream: BaseStream, range: str):
    """
    generate streaming response based on stream information

    :param stream: stream-information
    :param range:  http header containing byte-range
    """
    info, stream = stream
    if isinstance(stream, str):
        return RedirectResponse(stream, status_code=302)
    # generate generic response
    chunk = info.bitrate or 1024**2
    start, end, status, headers = 0, info.size - 1, 200, {
        'Content-Type':     info.meta.mime,
        'Accept-Ranges':    'bytes',
        'Content-Encoding': 'identity',
        'Content-Length':   str(info.size),
        'Access-Control-Expose-Headers': (
            'Content-Type, Accept-Ranges, Content-Length, '
            'Content-Range, Content-Encoding'
        ),
    }
    # handle byte-range is supplied
    if range is not None:
        status     = 206
        start, end = parse_range_header(range, info.size)
        headers['Content-Length'] = str(end - start + 1)
        headers['Content-Range']  = f'bytes {start}-{end}/{info.size}'
    return StreamingResponse(
        read_chunked_range(stream, start, end, chunk),
        headers=headers,
        status_code=status,
    )

#** Routes **#

@api.get('/stream/{id}/player')
def player(req: Request, id: str):
    """"""
    return HTMLResponse(content=f"""
<center>
    <audio controls src="{req.url_for('stream_audio', id=id)}"></audio>
</center>
""")

@api.get('/stream/{id}')
def stream_audio(id: str, range: str = Header(None)):
    """
    stream audio content via a chunked range of bytes

    :param id:    track-id to retrieve and play
    :param range: `Range` http-header
    :return:      chunked audio content
    """
    content = Context.audio_backend.stream_track(id)
    if content is None:
        raise HTTPException(status_code=400, detail='Invalid Track ID')
    return streaming_response(content, range)

@api.get('/info/all')
def audio_info_all(page: int = 1, size: int = 50) -> PagedAudio:
    """
    retrieve list of all tracks in the database

    :param page: page number on paginated results
    :param size: page-size on paginated results
    :return:     list of all possible tracks and thier info
    """
    info_page = Context.audio_backend.all_tracks(page, size)
    items     = [info.meta for info in info_page]
    return PagedAudio(items=items, page=page, size=len(items))

@api.get('/info/id/{id}')
def audio_info(id: str) -> Optional[AudioMeta]:
    """
    retrieve details for the specifed track-id

    :param id: track-id associated w/ retrieved details
    :return:   json of track details
    """
    info = Context.audio_backend.get_track(id)
    if info is None:
        raise HTTPException(400, detail='no such track')
    return info.meta

@api.get('/search')
def audio_info_search(search: UserSearch = Depends()) -> List[AudioMeta]:
    """
    retrieve list of track-ids associated w/ given search

    :param search: search query params
    :return:       json list of track details
    """
    info_search = Context.audio_backend.search_tracks(search)
    return [info.meta for info in info_search]

@api.get('/categories')
def audio_categories() -> Set[str]:
    """
    retrieve categories available for backend
    """
    return Context.audio_backend.get_categories()
