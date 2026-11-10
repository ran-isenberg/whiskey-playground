"""What the LLM returns (D8): ids, scores, reasons, serving. Never bottle details or orders."""

from pydantic import BaseModel, Field


class Pick(BaseModel):
    """One recommended bottle from the search results."""

    id: str = Field(description='Inventory id exactly as returned by search_inventory, e.g. lagavulin-16')
    match_score: int = Field(description='0-100 per the rubric (code clamps out-of-range values)')
    why: str = Field(description="2-4 sentences tying the user's own words to this whiskey's specific traits")
    serving: str = Field(description='One short serving suggestion')


class AgentAnswer(BaseModel):
    """The sommelier's answer for this turn."""

    message: str = Field(description='1-2 sentences in the bartender persona. Details go in picks, not here.')
    picks: list[Pick] = Field(
        default_factory=list,
        description='Best first, at most 3. Empty for off-topic, distress, or when nothing fits.',
    )
