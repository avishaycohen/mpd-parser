#!/usr/bin/env python3
"""
Benchmark mpegdash (DOM/minidom-based) parsing speed.

Usage:
  python scripts/bench_mpegdash.py --file manifest.mpd
  python scripts/bench_mpegdash.py --url  https://.../manifest.mpd

Options:
  --iters   Number of timed iterations (default: 300)
  --warmup  Number of warmup iterations (default: 50)
"""

from __future__ import annotations

import argparse
import time
import urllib.request
from typing import Any, Iterable, List, Optional, Set, Tuple

from mpegdash.parser import MPEGDASHParser


def read_bytes_from_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "techtalk-benchmark/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def read_text(path: Optional[str], url: Optional[str]) -> str:
    if bool(path) == bool(url):
        raise SystemExit("Provide exactly one of --file or --url")

    if path:
        with open(path, "rb") as f:
            data = f.read()
    else:
        data = read_bytes_from_url(url)  # type: ignore[arg-type]

    return data.decode("utf-8", errors="replace")


def safe_iter(x: Any) -> Iterable[Any]:
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        return x
    return []


def walk_obj_collect_bandwidths(obj: Any) -> Tuple[int, List[int]]:
    """
    mpegdash returns an object model (DOM-derived).
    We try common access patterns first, then fall back to a generic object walk.

    Returns:
      (representation_count_guess, bandwidth_values)
    """
    # 1) Try "standard looking" structure:
    # mpd.periods -> period.adaptation_sets -> aset.representations
    bws: List[int] = []
    rep_count = 0

    try:
        for period in safe_iter(getattr(obj, "periods", None)):
            for aset in safe_iter(getattr(period, "adaptation_sets", None)):
                reps = safe_iter(getattr(aset, "representations", None))
                rep_count += len(list(reps)) if isinstance(reps, list) else 0
                for rep in reps:
                    bw = getattr(rep, "bandwidth", None)
                    if bw is not None:
                        try:
                            bws.append(int(bw))
                        except ValueError:
                            pass
        if bws:
            return (rep_count or len(bws)), bws
    except Exception:
        pass

    # 2) Fallback: generic object graph walk; collect attrs named "bandwidth"
    seen: Set[int] = set()
    stack: List[Any] = [obj]
    while stack:
        cur = stack.pop()
        oid = id(cur)
        if oid in seen:
            continue
        seen.add(oid)

        # collect bandwidth if present
        bw = getattr(cur, "bandwidth", None)
        if bw is not None:
            try:
                bws.append(int(bw))
            except Exception:
                pass

        # walk attributes
        try:
            d = getattr(cur, "__dict__", None)
            if isinstance(d, dict):
                for v in d.values():
                    if isinstance(v, (str, int, float, bytes, bool)) or v is None:
                        continue
                    if isinstance(v, (list, tuple)):
                        stack.extend(v)
                    else:
                        stack.append(v)
        except Exception:
            continue

    # representation count is approximated by bandwidth count here
    return (len(bws), bws)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="Path to MPD file")
    ap.add_argument("--url", help="URL to MPD")
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--warmup", type=int, default=50)
    args = ap.parse_args()

    mpd_xml = read_text(args.file, args.url)

    # Warmup
    for _ in range(args.warmup):
        _ = MPEGDASHParser.parse(mpd_xml)

    # Timed
    t0 = time.perf_counter()
    last_obj = None
    for _ in range(args.iters):
        last_obj = MPEGDASHParser.parse(mpd_xml)
    t1 = time.perf_counter()

    if last_obj is None:
        raise SystemExit("Unexpected: no parse result")

    rep_count, bandwidths = walk_obj_collect_bandwidths(last_obj)
    bandwidths_sorted = sorted(bandwidths)

    total_s = t1 - t0
    avg_ms = (total_s / args.iters) * 1000.0

    print("\n== mpegdash benchmark ==")
    if args.file:
        print(f"input: file  {args.file}")
    else:
        print(f"input: url   {args.url}")

    print(f"warmup: {args.warmup}")
    print(f"iters:  {args.iters}")
    print(f"reps:   {rep_count} (best-effort)")
    if bandwidths_sorted:
        print(f"bandwidth sample (bps): {bandwidths_sorted[:8]}")
        print(f"bandwidth max (bps):    {bandwidths_sorted[-1]}")
    else:
        print("bandwidth sample (bps): <none found>")

    print(f"total:  {total_s:.4f}s")
    print(f"avg:    {avg_ms:.3f} ms/parse\n")


if __name__ == "__main__":
    main()