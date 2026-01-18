from typing import Literal
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import httpx
from .settings import settings


_token: dict[str, str] | None = None


def get_stream_id(channel: str):
    response = httpx.get(
        f"https://www.youtube.com/{channel}/live",
        params={"ucbcb": 1},
        follow_redirects=True,
    )
    soup = BeautifulSoup(response.text, features="html.parser")
    link = soup.find("link", rel="canonical")
    if link is None:
        return None
    parsed = urlparse(link["href"])
    video = parse_qs(parsed.query)
    if "v" in video:
        return video["v"][0]


async def get_video_id(channel: str):
    response = await youtube_api(
        "get", f"channels?path=contentDetails&forHandle={channel}"
    )
    print(response.json())
    return None


async def get_viewer_count(video_id: str):
    response = await youtube_api(
        "get", f"videos?part=liveStreamingDetails&id={video_id}"
    )
    j_resp = response.json()
    if "items" in j_resp:
        return int(j_resp["items"][0]["liveStreamingDetails"]["concurrentViewers"])
    return 0


async def youtube_api(
    method: Literal["get"] | Literal["post"], url: str
) -> httpx.Response:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    client = httpx.AsyncClient(params={**qs, "key": settings.youtube_api_key})
    return await getattr(client, method)(
        f"https://www.googleapis.com/youtube/v3/{parsed.path}",
    )


async def get_youtube_view_count(channel: str):
    video_id = get_stream_id(channel)
    print(video_id)

    if video_id is None:
        return 0
    viewers = await get_viewer_count(video_id)
    return viewers
