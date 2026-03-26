import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import Settings
from app.domain.enums import Platform


@dataclass
class OAuthTokens:
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    metadata: dict[str, Any]


class OAuthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_authorization_url(self, platform: Platform, user_id: str) -> tuple[str, str]:
        state = secrets.token_urlsafe(24)
        if platform == Platform.X:
            base_url = "https://twitter.com/i/oauth2/authorize"
            query = {
                "response_type": "code",
                "client_id": self.settings.x_client_id,
                "redirect_uri": self.settings.x_redirect_uri,
                "scope": "tweet.read tweet.write users.read offline.access",
                "state": f"{user_id}:{state}",
                "code_challenge": "replace-with-pkce",
                "code_challenge_method": "plain",
            }
        else:
            base_url = "https://www.linkedin.com/oauth/v2/authorization"
            query = {
                "response_type": "code",
                "client_id": self.settings.linkedin_client_id,
                "redirect_uri": self.settings.linkedin_redirect_uri,
                "scope": "openid profile email w_member_social",
                "state": f"{user_id}:{state}",
            }
        return f"{base_url}?{urlencode(query)}", state

    async def exchange_code(self, platform: Platform, code: str) -> OAuthTokens:
        if platform == Platform.X:
            return await self._post_token(
                "https://api.x.com/2/oauth2/token",
                {
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.settings.x_redirect_uri,
                    "client_id": self.settings.x_client_id,
                    "code_verifier": "replace-with-pkce",
                },
            )
        return await self._post_token(
            "https://www.linkedin.com/oauth/v2/accessToken",
            {
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.settings.linkedin_redirect_uri,
                "client_id": self.settings.linkedin_client_id,
                "client_secret": self.settings.linkedin_client_secret,
            },
        )

    async def _post_token(self, url: str, data: dict[str, Any]) -> OAuthTokens:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            payload = response.json()
        expires_at = None
        if payload.get("expires_in"):
            expires_at = datetime.utcnow() + timedelta(seconds=int(payload["expires_in"]))
        return OAuthTokens(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            expires_at=expires_at,
            metadata=payload,
        )
