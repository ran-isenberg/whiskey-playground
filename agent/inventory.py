"""inventory.json loading (KB-6) and lookups."""

import json
import logging

import boto3

log = logging.getLogger(__name__)

Inventory = dict[str, dict]


def load_inventory(bucket: str, key: str) -> Inventory:
    body = boto3.client('s3').get_object(Bucket=bucket, Key=key)['Body'].read()
    inv = json.loads(body)
    log.info('loaded inventory: %d whiskeys', len(inv))
    return inv
