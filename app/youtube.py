from datetime import datetime
from typing import Literal
from authlib.integrations.httpx_client import AsyncOAuth2Client
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import httpx
from .settings import settings


_token: dict[str, str] | None = None


def get_stream_id(channel: str):
    response = httpx.get(
        f"https://www.youtube.com/c/{channel}/live",
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


def _get_client(token: dict[str, str] | None = None) -> AsyncOAuth2Client:
    return AsyncOAuth2Client(
        client_id=settings.twitch_client_id,
        client_secret=settings.twitch_client_secret,
        token=token,
        token_endpoint="https://id.twitch.tv/oauth2/token",
        token_endpoint_auth_method="client_secret_post",
    )


async def twitch_api(
    method: Literal["get"] | Literal["post"], url: str
) -> httpx.Response:
    client = _get_client(await get_twitch_token())
    return await getattr(client, method)(
        f"https://api.twitch.tv/helix/{url}",
        headers={"Client-Id": settings.twitch_client_id},
    )


async def get_twitch_token():
    global _token
    if _token is not None:
        expiration = datetime.fromtimestamp(_token.get("expires_at", 0))
        if expiration > datetime.now():
            return _token

    client = _get_client()
    _token = await client.fetch_token()
    return _token


async def get_youtube_view_count(channel: str):
    stream_id = get_stream_id(channel)
    if stream_id is None:
        return 0
    return 0
