"""search_inventory tool (AG-13): Bedrock KB Retrieve with the in-stock filter always on."""

from __future__ import annotations

import logging
from collections.abc import Callable

import boto3
from strands import tool

log = logging.getLogger(__name__)

IN_STOCK = {'equals': {'key': 'in_stock', 'value': True}}
TEXT_LIMIT = 1200


def build_filter(max_price_level: int | None) -> dict:
    if max_price_level is None:
        return IN_STOCK
    n = max(1, min(4, int(max_price_level)))
    return {'andAll': [IN_STOCK, {'lessThanOrEquals': {'key': 'price_level', 'value': n}}]}


def compact(results: list[dict]) -> list[dict]:
    out = []
    for r in results:
        meta = r.get('metadata', {}) or {}
        wid = meta.get('id')
        if not wid:
            continue
        out.append(
            {
                'id': wid,
                'price_tier': meta.get('price_tier'),
                'score': round(float(r.get('score', 0.0)), 3),
                'text': (r.get('content', {}).get('text') or '')[:TEXT_LIMIT],
            }
        )
    return out


def make_search_tool(kb_id: str, k: int, region: str, on_results: Callable[[str, int | None, list[str]], None]):
    """Build the tool bound to this session (on_results records retrieved ids for the turn log)."""
    client = boto3.client('bedrock-agent-runtime', region_name=region)

    @tool
    def search_inventory(query: str, max_price_level: int | None = None) -> list[dict]:
        """Semantic search of our in-stock whiskey inventory. Always call this before recommending.

        Args:
            query: Mood, occasion and flavor words describing what the user wants.
            max_price_level: Price ceiling. 1=$ (under $40), 2=$$ ($40-80), 3=$$$ ($80-150), 4=$$$$ ($150+).
                Set it when the user states a budget or asks for something cheaper.
        """
        resp = client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': k, 'filter': build_filter(max_price_level)}},
        )
        hits = compact(resp.get('retrievalResults', []))
        on_results(query, max_price_level, [h['id'] for h in hits])
        log.info('search_inventory query=%r max_price_level=%s -> %s', query, max_price_level, [h['id'] for h in hits])
        return hits

    return search_inventory
