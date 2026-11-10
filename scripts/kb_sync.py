"""make kb-sync: build sidecars + inventory.json from kb/, upload to S3, run KB ingestion (KB-3).

Usage:
    uv run scripts/kb_sync.py            # build, upload, ingest
    uv run scripts/kb_sync.py --dry-run  # build only, write to build/kb
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / 'kb'
STACK_NAME = 'WhiskeyAgentStack'

PRICE_LEVEL = {'$': 1, '$$': 2, '$$$': 3, '$$$$': 4}
REQUIRED = [
    'id',
    'name',
    'distillery',
    'country',
    'region',
    'type',
    'age',
    'abv',
    'price_tier',
    'rating',
    'in_stock',
    'flavor_profile',
    'mood_tags',
    'occasion_tags',
    'serving_suggestions',
]
SIDECAR_FIELDS = ['id', 'in_stock', 'price_level', 'price_tier', 'type', 'country', 'rating']
NOTE_RE = re.compile(r'^- \*\*(Nose|Palate|Finish):\*\*\s*(.+)$', re.MULTILINE)


class KbError(ValueError):
    pass


def parse_file(path: Path) -> tuple[dict, str]:
    """Return (frontmatter, body) for one kb markdown file."""
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---'):
        raise KbError(f'{path.name}: missing frontmatter')
    _, fm, body = text.split('---', 2)
    return yaml.safe_load(fm), body.strip()


def build_record(path: Path) -> dict:
    """Validate one file and return its inventory record."""
    fm, body = parse_file(path)
    missing = [f for f in REQUIRED if f not in fm]
    if missing:
        raise KbError(f'{path.name}: missing fields {missing}')
    if fm['id'] != path.stem:
        raise KbError(f'{path.name}: id {fm["id"]!r} does not match filename')
    if fm['price_tier'] not in PRICE_LEVEL:
        raise KbError(f'{path.name}: bad price_tier {fm["price_tier"]!r}')
    notes = {k.lower(): v.strip() for k, v in NOTE_RE.findall(body)}
    if set(notes) != {'nose', 'palate', 'finish'}:
        raise KbError(f'{path.name}: tasting notes incomplete ({sorted(notes)})')
    record = {f: fm[f] for f in REQUIRED}
    record['price_level'] = PRICE_LEVEL[fm['price_tier']]
    record['tasting_notes'] = notes
    return record


def sidecar(record: dict) -> dict:
    return {'metadataAttributes': {f: record[f] for f in SIDECAR_FIELDS}}


def build_all(kb_dir: Path = KB_DIR) -> dict[str, dict]:
    inventory: dict[str, dict] = {}
    for path in sorted(kb_dir.glob('*.md')):
        if path.name.lower() == 'readme.md':
            continue
        rec = build_record(path)
        inventory[rec['id']] = rec
    if not inventory:
        raise KbError('no whiskey files found')
    return inventory


def stack_outputs() -> dict[str, str]:
    import boto3

    cfn = boto3.client('cloudformation')
    stack = cfn.describe_stacks(StackName=STACK_NAME)['Stacks'][0]
    return {o['OutputKey']: o['OutputValue'] for o in stack.get('Outputs', [])}


def upload_and_ingest(inventory: dict[str, dict]) -> None:
    import boto3

    out = stack_outputs()
    bucket, kb_id, ds_id = out['DataBucketName'], out['KnowledgeBaseId'], out['DataSourceId']
    s3 = boto3.client('s3')
    agent = boto3.client('bedrock-agent')

    wanted: set[str] = set()
    for wid, rec in inventory.items():
        src = (KB_DIR / f'{wid}.md').read_bytes()
        key = f'docs/{wid}.md'
        s3.put_object(Bucket=bucket, Key=key, Body=src, ContentType='text/markdown')
        s3.put_object(Bucket=bucket, Key=f'{key}.metadata.json', Body=json.dumps(sidecar(rec)).encode(), ContentType='application/json')
        wanted |= {key, f'{key}.metadata.json'}

    stale = []
    for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix='docs/'):
        stale += [o['Key'] for o in page.get('Contents', []) if o['Key'] not in wanted]
    for key in stale:
        s3.delete_object(Bucket=bucket, Key=key)

    s3.put_object(Bucket=bucket, Key='inventory/inventory.json', Body=json.dumps(inventory).encode(), ContentType='application/json')
    print(f'uploaded {len(inventory)} whiskeys (+sidecars, inventory.json), removed {len(stale)} stale keys')

    job = agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)['ingestionJob']
    job_id = job['ingestionJobId']
    print(f'ingestion job {job_id} started')
    while True:
        job = agent.get_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id, ingestionJobId=job_id)['ingestionJob']
        status = job['status']
        if status in ('COMPLETE', 'FAILED', 'STOPPED'):
            break
        time.sleep(5)
    print(f'ingestion {status}: {json.dumps(job.get("statistics", {}))}')
    if status != 'COMPLETE' or job.get('statistics', {}).get('numberOfDocumentsFailed', 0):
        print(json.dumps(job.get('failureReasons', []), indent=2))
        sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    inventory = build_all()
    out_of_stock = [k for k, v in inventory.items() if not v['in_stock']]
    print(f'built {len(inventory)} records, out of stock: {out_of_stock}')
    if args.dry_run:
        out = ROOT / 'build' / 'kb'
        out.mkdir(parents=True, exist_ok=True)
        (out / 'inventory.json').write_text(json.dumps(inventory, indent=2))
        print(f'wrote {out / "inventory.json"}')
        return
    upload_and_ingest(inventory)


if __name__ == '__main__':
    main()
