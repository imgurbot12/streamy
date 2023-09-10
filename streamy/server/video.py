"""
Streamy Server `Video` API
"""
from typing import *

from fastapi import Depends, Header, HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

from streamy.server.backend import UserSearch

from . import Context
from .track import streaming_response 
from ..utils import VideoMeta, PagedList, BluePrint

#** Variables **#
__all__ = ['api']

api = BluePrint('/api/v1/video/')

class PagedVideo(PagedList[VideoMeta]):
    pass

#** Routes **#

@api.get('/stream/{id}/player')
def player(req: Request, id: str):
    """"""
    return HTMLResponse(content=f"""
<center>
    <video controls src="{req.url_for('stream_video', id=id)}"></video>
</center>
""")

@api.get('/stream/{id}')
def stream_video(id: str, range: str = Header(None)):
    """
    stream video content via a chunked range of bytes

    :param id:    track-id to retrieve and play
    :param range: `Range` http-header
    :return:      chunked audio content
    """
    # retrieve stream content
    content = Context.video_backend.stream_video(id)
    if content is None:
        raise HTTPException(status_code=400, detail='Invalid Video ID')
    return streaming_response(content, range) 

@api.get('/info/all')
def video_info_all(page: int = 1, size: int = 50) -> PagedVideo:
    """
    retrieve list of all tracks in the database

    :param page: page number on paginated results
    :param size: page-size on paginated results
    :return:    list of all possible tracks and thier info
    """
    info_page = Context.video_backend.all_videos(page, size)
    items     = [info.meta for info in info_page]
    return PagedVideo(items=items, page=page, size=len(items))

@api.get('/info/id/{id}')
def video_info(id: str) -> Optional[VideoMeta]:
    """
    retrieve details for the specifed track-id

    :param id: track-id associated w/ retrieved details
    :return:   json of track details
    """
    info = Context.video_backend.get_video(id)
    if info is None:
        raise HTTPException(400, detail='no such track')
    return info.meta

@api.get('/search')
def video_info_search(search: UserSearch = Depends()) -> List[VideoMeta]:
    """
    retrieve list of video-ids associated w/ given search

    :param search: search query params
    :return:       json list of track details
    """
    info_search = Context.video_backend.search_videos(search)
    return [info.meta for info in info_search]

@api.get('/categories')
def video_categories() -> Set[str]:
    """
    retrieve categories available for backend
    """
    return Context.video_backend.get_categories()
