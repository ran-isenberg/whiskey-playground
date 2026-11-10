from answer import AgentAnswer, Pick
from contract import ChatResponse
from recommend.check_and_fill import ZERO_MATCH_FALLBACK, check_and_fill

SID = '3f6c1d2e-8a4b-4c1e-9f7a-2b5d8e0c4a91'


def pick(id, score, why='Because you said rainy.', serving='Neat.'):
    return Pick(id=id, match_score=score, why=why, serving=serving)


def run(picks, inventory, message="Here is what I'd pour.", threshold=50, n=3):
    return check_and_fill(AgentAnswer(message=message, picks=picks), inventory, SID, threshold=threshold, max_matches=n)


def test_unknown_id_dropped(inventory):
    resp, dropped = run([pick('pappy-van-winkle-23', 99), pick('lagavulin-16', 90)], inventory)
    assert [m.id for m in resp.matches] == ['lagavulin-16']
    assert {'id': 'pappy-van-winkle-23', 'reason': 'unknown_id', 'score': 99} in dropped


def test_out_of_stock_dropped(inventory):
    resp, dropped = run([pick('yamazaki-12', 95), pick('hakushu-12', 80)], inventory)
    assert [m.id for m in resp.matches] == ['hakushu-12']
    assert dropped[0]['reason'] == 'out_of_stock'


def test_duplicates_removed(inventory):
    resp, dropped = run([pick('talisker-10', 80), pick('talisker-10', 70)], inventory)
    assert [m.id for m in resp.matches] == ['talisker-10']
    assert dropped[0]['reason'] == 'duplicate'


def test_below_threshold_dropped(inventory):
    resp, dropped = run([pick('talisker-10', 49), pick('oban-14', 50)], inventory)
    assert [m.id for m in resp.matches] == ['oban-14']
    assert dropped[0]['reason'] == 'below_threshold'


def test_clamp_sort_and_cut(inventory):
    picks = [pick('oban-14', 60), pick('talisker-10', 150), pick('ardbeg-10', 75), pick('lagavulin-16', 90)]
    resp, dropped = run(picks, inventory)
    assert [(m.rank, m.id, m.match_score) for m in resp.matches] == [(1, 'talisker-10', 100), (2, 'lagavulin-16', 90), (3, 'ardbeg-10', 75)]
    assert {'id': 'oban-14', 'reason': 'over_max', 'score': 60} in dropped


def test_ties_keep_model_order(inventory):
    resp, _ = run([pick('oban-14', 80), pick('talisker-10', 80)], inventory)
    assert [m.id for m in resp.matches] == ['oban-14', 'talisker-10']


def test_n_configurable(inventory):
    resp, _ = run([pick('oban-14', 80), pick('talisker-10', 70)], inventory, n=1)
    assert [m.id for m in resp.matches] == ['oban-14']


def test_card_fields_from_inventory(inventory):
    resp, _ = run([pick('lagavulin-16', 92)], inventory)
    w = resp.matches[0].whiskey
    rec = inventory['lagavulin-16']
    for f in ('name', 'distillery', 'country', 'region', 'type', 'age', 'abv', 'price_tier', 'rating', 'flavor_profile'):
        assert getattr(w, f) == rec[f]
    assert w.tasting_notes.model_dump() == rec['tasting_notes']
    ChatResponse.model_validate(resp.model_dump())
    assert resp.pending_order is None and resp.order is None


def test_zero_match_fallback_when_all_dropped(inventory):
    resp, _ = run([pick('pappy-van-winkle-23', 99)], inventory, message='Here are my picks for you!')
    assert resp.matches == [] and resp.message == ZERO_MATCH_FALLBACK


def test_keeps_steer_message_when_no_picks(inventory):
    resp, _ = run([], inventory, message='I only pour whiskey, but tell me your mood!')
    assert resp.matches == [] and resp.message.startswith('I only pour whiskey')
