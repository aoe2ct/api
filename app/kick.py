from datetime import datetime
from typing import Literal
from authlib.integrations.httpx_client import AsyncOAuth2Client
import httpx


from .settings import settings


_token: dict[str, str | int] | None = None


def _get_client(token: dict[str, str | int] | None = None) -> AsyncOAuth2Client:
    return AsyncOAuth2Client(
        client_id=settings.kick_client_id,
        client_secret=settings.kick_client_secret,
        token=token,
        token_endpoint="https://id.kick.com/oauth/token",
        token_endpoint_auth_method="client_secret_post",
    )


async def kick_api(
    method: Literal["get"] | Literal["post"], url: str
) -> httpx.Response:
    client = _get_client(await get_kick_token())
    return await getattr(client, method)(
        f"https://api.kick.com/public/v1/{url}",
        headers={"Client-Id": settings.twitch_client_id},
    )


async def get_kick_token() -> dict[str, str | int]:
    global _token
    if _token is not None:
        expiration = datetime.fromtimestamp(_token.get("expires_at", 0))
        if expiration > datetime.now():
            return _token

    client = _get_client()
    _token = await client.fetch_token()
    return _token


async def get_kick_view_count(slug: str):
    response = await kick_api("get", f"channels?slug={slug}")
    channels = response.json()
    for channel in channels["data"]:
        if channel["slug"] == slug:
            return channel["stream"]["viewer_count"]
    return 0
