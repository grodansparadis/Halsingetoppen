#!/usr/bin/env python3
"""Batch-match YouTube Music artist links for artists in the local SQLite database."""

import argparse
import re
import sqlite3
import sys
import time
from difflib import SequenceMatcher

from ytmusicapi import YTMusic

DB_PATH = "toppen.sqlite3"


def normalize_name(value: str) -> str:
    value = (value or "").lower().strip()
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value


def similarity_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def extract_candidate_name(item: dict) -> str:
    if isinstance(item.get("artist"), str):
        return item.get("artist", "").strip()

    if item.get("artist") and isinstance(item.get("artist"), dict):
        return (item["artist"].get("name") or "").strip()

    artists = item.get("artists")
    if isinstance(artists, list) and artists:
        first = artists[0]
        if isinstance(first, dict):
            return (first.get("name") or "").strip()

    return (item.get("name") or "").strip()


def extract_browse_id(item: dict) -> str:
    direct_browse_id = item.get("browseId")
    if isinstance(direct_browse_id, str) and direct_browse_id.strip():
        return direct_browse_id.strip()

    artist = item.get("artist")
    if isinstance(artist, dict) and artist.get("id"):
        return artist["id"]

    artists = item.get("artists")
    if isinstance(artists, list) and artists:
        first = artists[0]
        if isinstance(first, dict) and first.get("id"):
            return first["id"]

    browse_id = item.get("id")
    return (browse_id or "").strip()


def get_best_youtube_music_match(ytmusic: YTMusic, artist_name: str, limit: int = 10):
    results = ytmusic.search(artist_name, filter="artists", limit=limit)

    target = normalize_name(artist_name)
    best_item = None
    best_score = 0.0

    for item in results:
        candidate_name = extract_candidate_name(item)
        candidate = normalize_name(candidate_name)

        score = similarity_score(target, candidate)

        if target == candidate:
            score += 0.4
        elif target in candidate or candidate in target:
            score += 0.2

        if score > best_score:
            best_score = score
            best_item = item

    if not best_item:
        return None, 0.0, ""

    browse_id = extract_browse_id(best_item)
    candidate_name = extract_candidate_name(best_item)

    if browse_id.startswith("UC"):
        url = f"https://music.youtube.com/channel/{browse_id}"
    elif browse_id:
        url = f"https://music.youtube.com/browse/{browse_id}"
    else:
        url = ""

    return best_item, best_score, url


def match_all_youtube_links(db_path: str, min_score: float, dry_run: bool, delay: float):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    artists = conn.execute(
        """
        SELECT id, name, youtube_music_link
        FROM artists
        WHERE (youtube_music_link IS NULL OR TRIM(youtube_music_link) = '')
          AND name IS NOT NULL
          AND TRIM(name) != ''
        ORDER BY name COLLATE NOCASE
        """
    ).fetchall()

    ytmusic = YTMusic()

    total = len(artists)
    matched = 0
    skipped_low_score = 0
    errors = 0

    print(f"Checking {total} artists without YouTube Music link...")

    for index, artist in enumerate(artists, start=1):
        artist_id = artist["id"]
        artist_name = artist["name"]

        try:
            item, score, youtube_url = get_best_youtube_music_match(ytmusic, artist_name)
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

        candidate_name = extract_candidate_name(item)

        if score < min_score or not youtube_url:
            skipped_low_score += 1
            print(
                f"[{index}/{total}] SKIP {artist_name} -> {candidate_name or '-'} (score {score:.2f})"
            )
            time.sleep(delay)
            continue

        matched += 1

        if not dry_run:
            conn.execute(
                "UPDATE artists SET youtube_music_link = ? WHERE id = ?",
                [youtube_url, artist_id],
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
        description="Match missing YouTube Music links for artists in toppen.sqlite3"
    )
    parser.add_argument("--db", default=DB_PATH, help="Path to SQLite database")
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.90,
        help="Minimum matching score (0-1) required to update",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show potential matches without updating database",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.25,
        help="Delay between requests in seconds",
    )
    args = parser.parse_args()

    if args.min_score < 0 or args.min_score > 1:
        print("--min-score must be between 0 and 1", file=sys.stderr)
        sys.exit(2)

    match_all_youtube_links(
        db_path=args.db,
        min_score=args.min_score,
        dry_run=args.dry_run,
        delay=args.delay,
    )


if __name__ == "__main__":
    main()
