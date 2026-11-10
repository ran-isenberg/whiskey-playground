import json

import pytest

import kb_sync


def test_all_files_parse(inventory):
    assert len(inventory) == 59
    assert sorted(k for k, v in inventory.items() if not v['in_stock']) == ['blantons-original', 'midleton-very-rare', 'yamazaki-12']


def test_price_level_mapping(inventory):
    for rec in inventory.values():
        assert rec['price_level'] == {'$': 1, '$$': 2, '$$$': 3, '$$$$': 4}[rec['price_tier']]


def test_tasting_notes_parsed(inventory):
    notes = inventory['lagavulin-16']['tasting_notes']
    assert set(notes) == {'nose', 'palate', 'finish'}
    assert notes['nose'].startswith('Thick peat smoke')


def test_sidecar_shape(inventory):
    sc = kb_sync.sidecar(inventory['lagavulin-16'])
    assert sc == {
        'metadataAttributes': {
            'id': 'lagavulin-16',
            'in_stock': True,
            'price_level': 3,
            'price_tier': '$$$',
            'type': 'Single Malt Scotch',
            'country': 'Scotland',
            'rating': 89,
        }
    }
    json.dumps(sc)


def test_missing_field_fails(tmp_path):
    src = (kb_sync.KB_DIR / 'lagavulin-16.md').read_text().replace('rating: 89\n', '')
    (tmp_path / 'lagavulin-16.md').write_text(src)
    with pytest.raises(kb_sync.KbError, match='rating'):
        kb_sync.build_all(tmp_path)


def test_id_must_match_filename(tmp_path):
    (tmp_path / 'other.md').write_text((kb_sync.KB_DIR / 'lagavulin-16.md').read_text())
    with pytest.raises(kb_sync.KbError, match='filename'):
        kb_sync.build_all(tmp_path)
