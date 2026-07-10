"""Tiny on-disk cache so paid/slow scorers (Pangram, the judge) never pay twice
for the same (scorer, model, text) triple. Critical for staying inside the
600-credit/month Pangram budget: a re-run of an unchanged output costs 0.

`load`/`store` are exposed so batched scoring can populate the cache per-reply
(one API call fills many cache entries), while `cached` remains the simple
compute-if-missing path. All three share the same key scheme, so a reply scored
in a batch is a cache hit for a later single-text lookup and vice versa.
"""

from __future__ import annotations

import hashlib
import json
import os

import config


def _key(namespace: str, payload: str) -> str:
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
    return f"{namespace}_{h}"


def _path(namespace: str, payload: str) -> str:
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    return os.path.join(config.CACHE_DIR, _key(namespace, payload) + ".json")


def load(namespace: str, payload: str):
    """Return the cached value for `payload`, or None on a miss."""
    path = _path(namespace, payload)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def store(namespace: str, payload: str, value):
    """Write `value` to the cache and return it."""
    with open(_path(namespace, payload), "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
    return value


def cached(namespace: str, payload: str, compute):
    """Return cached result for `payload`, else compute it once and store it.

    `compute` is a zero-arg callable run only on a cache miss.
    """
    hit = load(namespace, payload)
    if hit is not None:
        return hit
    return store(namespace, payload, compute())
