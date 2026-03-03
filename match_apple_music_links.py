#!/usr/bin/env python3
"""Batch-match Apple Music artist links for artists in the local SQLite database."""

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from difflib import SequenceMatcher

DB_PATH = "toppen.sqlite3"
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"


def fetch_json_with_retry(url: str, max_retries: int = 6):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Halsingetoppen/1.0 (AppleLinkMatcher)",
            "Accept": "application/json",
        },
    )

    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < max_retries:
                retry_after_header = exc.headers.get("Retry-After") if exc.headers else None
                retry_after = float(retry_after_header) if retry_after_header and retry_after_header.isdigit() else 2.0
                sleep_seconds = retry_after + (attempt * 0.7)
                time.sleep(sleep_seconds)
                continue

            if exc.code in (500, 502, 503, 504) and attempt < max_retries:
                sleep_seconds = 1.2 * (2 ** attempt)
                time.sleep(sleep_seconds)
                continue

            raise


def normalize_name(value: str) -> str:
    value = (value or "").lower().strip()
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value


def similarity_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def get_best_apple_artist_match(artist_name: str, country: str, limit: int = 10):
    params = {
        "term": artist_name,
        "entity": "musicArtist",
        "country": country,
        "limit": str(limit),
    }
    url = f"{ITUNES_SEARCH_URL}?{urllib.parse.urlencode(params)}"

    payload = fetch_json_with_retry(url)

    normalized_target = normalize_name(artist_name)
    best_item = None
    best_score = 0.0

    for item in payload.get("results", []):
        candidate_name = item.get("artistName", "")
        normalized_candidate = normalize_name(candidate_name)

        score = similarity_score(normalized_target, normalized_candidate)

        if normalized_target == normalized_candidate:
            score += 0.4
        elif normalized_target in normalized_candidate or normalized_candidate in normalized_target:
            score += 0.2

        if score > best_score:
            best_score = score
            best_item = item

    if not best_item:
        return None, 0.0

    return best_item, best_score


def match_all_apple_links(db_path: str, min_score: float, country: str, dry_run: bool, delay: float):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    artists = conn.execute(
        """
        SELECT id, name, apple_music_link
        FROM artists
        WHERE (apple_music_link IS NULL OR TRIM(apple_music_link) = '')
          AND name IS NOT NULL
          AND TRIM(name) != ''
        ORDER BY name COLLATE NOCASE
        """
    ).fetchall()

    total = len(artists)
    matched = 0
    skipped_low_score = 0
    errors = 0

    print(f"Checking {total} artists without Apple Music link...")

    for index, artist in enumerate(artists, start=1):
        artist_id = artist["id"]
        artist_name = artist["name"]

        try:
            item, score = get_best_apple_artist_match(artist_name, country=country)
        except Exception as exc:
            errors += 1
            print(f"[{index}/{total}] ERROR {artist_name}: {exc}")
            time.sleep(delay)
            continue

        if not item:
            skipped_low_score += 1
            print(f"[{index}/{total}] NO MATCH {artist_name}")
            time.sleep(delay)
            continue

        artist_view_url = (
            item.get("artistViewUrl")
            or item.get("artistLinkUrl")
            or item.get("collectionViewUrl")
            or item.get("trackViewUrl")
            or ""
        ).strip()
        candidate_name = (item.get("artistName") or "").strip()

        if score < min_score or not artist_view_url:
            skipped_low_score += 1
            print(
                f"[{index}/{total}] SKIP {artist_name} -> {candidate_name or '-'} (score {score:.2f})"
            )
            time.sleep(delay)
            continue

        matched += 1

        if not dry_run:
            conn.execute(
                "UPDATE artists SET apple_music_link = ? WHERE id = ?",
                [artist_view_url, artist_id],
            )

        print(
            f"[{index}/{total}] MATCH {artist_name} -> {candidate_name} (score {score:.2f})"
        )
        time.sleep(delay)

    if not dry_run:
        conn.commit()

    conn.close()

    print("\nDone")
    print(f"- Total checked: {total}")
    print(f"- Matched: {matched}")
    print(f"- Skipped (low/no match): {skipped_low_score}")
    print(f"- Errors: {errors}")


def main():
    parser = argparse.ArgumentParser(
        description="Match missing Apple Music links for artists in toppen.sqlite3"
    )
    parser.add_argument("--db", default=DB_PATH, help="Path to SQLite database")
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.82,
        help="Minimum matching score (0-1) required to update",
    )
    parser.add_argument("--country", default="SE", help="Apple search country code")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show potential matches without updating database",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.12,
        help="Delay between requests in seconds",
    )
    args = parser.parse_args()

    if args.min_score < 0 or args.min_score > 1:
        print("--min-score must be between 0 and 1", file=sys.stderr)
        sys.exit(2)

    match_all_apple_links(
        db_path=args.db,
        min_score=args.min_score,
        country=args.country,
        dry_run=args.dry_run,
        delay=args.delay,
    )


if __name__ == "__main__":
    main()
