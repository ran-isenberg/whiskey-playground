from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

ErrorCode = Literal['INVALID_REQUEST', 'THROTTLED', 'TIMEOUT', 'AGENT_ERROR']


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=36, max_length=36)
    message: str = ''
    warmup: bool = False

    @field_validator('session_id')
    @classmethod
    def uuid_string(cls, v: str) -> str:
        if UUID(v).version != 4:
            raise ValueError('session_id must be a UUID4')
        return v

    @model_validator(mode='after')
    def message_rules(self):
        if not self.warmup:
            self.message = self.message.strip()
            if not 1 <= len(self.message) <= 500:
                raise ValueError('Message must be between 1 and 500 characters.')
        return self


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str


class ErrorBody(BaseModel):
    error: ErrorDetail
