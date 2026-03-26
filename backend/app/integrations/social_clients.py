from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.domain.enums import Platform


class RateLimitError(RuntimeError):
    pass


@dataclass
class PublishResult:
    platform_post_id: str
    payload: dict[str, Any]


class BaseSocialPublisher:
    platform: Platform

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, RateLimitError)),
        reraise=True,
    )
    async def publish(self, access_token: str, content: str, account_identifier: str) -> PublishResult:
        raise NotImplementedError

    async def _raise_for_limits(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            raise RateLimitError("Platform rate limit reached.")
        response.raise_for_status()


class XPublisher(BaseSocialPublisher):
    platform = Platform.X

    async def publish(self, access_token: str, content: str, account_identifier: str) -> PublishResult:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.x.com/2/tweets",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"text": content},
            )
            await self._raise_for_limits(response)
            payload = response.json()
        return PublishResult(platform_post_id=payload.get("data", {}).get("id", ""), payload=payload)


class LinkedInPublisher(BaseSocialPublisher):
    platform = Platform.LINKEDIN

    async def publish(self, access_token: str, content: str, account_identifier: str) -> PublishResult:
        body = {
            "author": f"urn:li:person:{account_identifier}",
            "commentary": content,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.linkedin.com/rest/posts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "LinkedIn-Version": "202405",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
                json=body,
            )
            await self._raise_for_limits(response)
            payload = response.json() if response.content else {}
        return PublishResult(platform_post_id=str(payload.get("id", "")), payload=payload)


def get_publisher(platform: Platform, settings: Settings) -> BaseSocialPublisher:
    if platform == Platform.X:
        return XPublisher(settings)
    return LinkedInPublisher(settings)
