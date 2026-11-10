"""Response contract (requirements §4). The UI depends only on this shape."""

from pydantic import BaseModel, Field


class TastingNotes(BaseModel):
    nose: str
    palate: str
    finish: str


class Whiskey(BaseModel):
    name: str
    distillery: str
    country: str
    region: str
    type: str
    age: int | None
    abv: float
    price_tier: str
    rating: int
    flavor_profile: list[str]
    tasting_notes: TastingNotes


class Match(BaseModel):
    rank: int = Field(ge=1)
    id: str
    match_score: int = Field(ge=0, le=100)
    why: str
    serving: str
    whiskey: Whiskey


class OrderLine(BaseModel):
    whiskey_id: str
    name: str
    quantity: int = Field(ge=1, le=6)


class PendingOrder(BaseModel):
    items: list[OrderLine] = Field(min_length=1, max_length=3)


class Order(BaseModel):
    order_id: str
    status: str
    items: list[OrderLine]


class ChatResponse(BaseModel):
    session_id: str
    message: str
    matches: list[Match] = Field(default_factory=list, max_length=3)
    pending_order: PendingOrder | None = None
    order: Order | None = None
