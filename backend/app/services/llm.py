from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.domain.enums import Platform
from app.services.prompts import PROMPT_TEMPLATES


@dataclass
class GeneratedPost:
    content: str
    metadata: dict[str, Any]


class PostValidationError(ValueError):
    pass


class LLMPostGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def generate(self, topic: str, tone: str, platform: Platform) -> GeneratedPost:
        prompt = PROMPT_TEMPLATES[platform.value].format(topic=topic, tone=tone)
        response = self.client.responses.create(
            model=self.settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": "Return one high-quality social media post. No markdown fences.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = (response.output_text or "").strip()
        self._validate(content, platform)
        return GeneratedPost(
            content=content,
            metadata={
                "model": self.settings.openai_model,
                "prompt": prompt,
                "response_id": response.id,
            },
        )

    def _validate(self, content: str, platform: Platform) -> None:
        if not content:
            raise PostValidationError("Generated content was empty.")
        if platform == Platform.X and len(content) > 280:
            raise PostValidationError("Generated X content exceeded 280 characters.")
