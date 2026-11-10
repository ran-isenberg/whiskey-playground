from recommend.tools import IN_STOCK, build_filter, compact


def test_in_stock_only():
    assert build_filter(None) == IN_STOCK


def test_price_filter_uses_andall():
    f = build_filter(2)
    assert f == {'andAll': [IN_STOCK, {'lessThanOrEquals': {'key': 'price_level', 'value': 2}}]}


def test_price_filter_clamped():
    assert build_filter(9)['andAll'][1]['lessThanOrEquals']['value'] == 4


def test_compact_skips_missing_id_and_truncates():
    hits = compact(
        [
            {'metadata': {'id': 'oban-14', 'price_tier': '$$'}, 'score': 0.51234, 'content': {'text': 'x' * 5000}},
            {'metadata': {}, 'content': {'text': 'no id'}},
        ]
    )
    assert len(hits) == 1 and hits[0]['id'] == 'oban-14' and len(hits[0]['text']) == 1200 and hits[0]['score'] == 0.512
