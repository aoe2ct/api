from datetime import datetime
from authlib.integrations.httpx_client import AsyncOAuth2Client
from typing import Literal
import httpx


from .settings import settings

_token: dict[str, str] | None = None


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


async def get_twitch_view_count(login: str | None):
    if login is None:
        return 0
    response = await twitch_api("get", f"streams?user_login={login}")
    streams = response.json()
    for stream in streams["data"]:
        if stream["user_login"] != login:
            continue
        return stream["viewer_count"]
    return 0
