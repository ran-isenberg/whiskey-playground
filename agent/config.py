"""Runtime settings from environment variables (AG-11). Change them with an agent redeploy only."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_id: str = 'us.anthropic.claude-haiku-5-5'
    # Claude 5 models reject `temperature` (deprecated), so it is only sent when TEMPERATURE is set.
    temperature: float | None = None
    max_matches: int = 3
    score_threshold: int = 50
    retrieve_k: int = 12
    kb_id: str = ''
    data_bucket: str = ''
    inventory_key: str = 'inventory/inventory.json'
    ordering_enabled: bool = False
    gateway_url: str = ''
    log_level: str = 'INFO'
    aws_region: str = 'us-east-1'

    @field_validator('temperature', mode='before')
    @classmethod
    def blank_is_none(cls, v):
        return None if v in ('', None) else v


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.max_matches = max(1, min(s.max_matches, 3))  # AG-2: hard maximum of 3
    return s
