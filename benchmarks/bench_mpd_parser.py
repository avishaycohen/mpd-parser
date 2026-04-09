#!/usr/bin/env python3
"""
Benchmark mpd-parser parsing speed (domain object model).

Usage:
  python scripts/bench_mpd_parser.py --file manifest.mpd
  python scripts/bench_mpd_parser.py --url  https://.../manifest.mpd
"""

from __future__ import annotations

import argparse
import time
import urllib.request
from typing import List, Optional, Tuple

from mpd_parser.parser import Parser


def read_bytes_from_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "techtalk-benchmark/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def read_text(path: Optional[str], url: Optional[str]) -> str:
    if bool(path) == bool(url):
        raise SystemExit("Provide exactly one of --file or --url")

    if path:
        data = open(path, "rb").read()
    else:
        data = read_bytes_from_url(url)  # type: ignore[arg-type]

    return data.decode("utf-8", errors="replace")


def extract_reps_and_bandwidths(mpd) -> Tuple[int, List[int]]:
    """
    mpd-parser domain model traversal.
    Assumes:
      mpd.periods -> period.adaptation_sets -> aset.representations
    """
    rep_count = 0
    bws: List[int] = []

    for period in getattr(mpd, "periods", []) or []:
        for aset in getattr(period, "adaptation_sets", []) or []:
            reps = getattr(aset, "representations", []) or []
            rep_count += len(reps)
            for rep in reps:
                bw = getattr(rep, "bandwidth", None)
                if bw is not None:
                    try:
                        bws.append(int(bw))
                    except ValueError:
                        pass

    return rep_count, bws


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
        _ = Parser.from_string(mpd_xml)

    # Timed
    t0 = time.perf_counter()
    last_mpd = None
    for _ in range(args.iters):
        last_mpd = Parser.from_string(mpd_xml)
    t1 = time.perf_counter()

    if last_mpd is None:
        raise SystemExit("Unexpected: no parse result")

    rep_count, bandwidths = extract_reps_and_bandwidths(last_mpd)
    bandwidths_sorted = sorted(bandwidths)

    total_s = t1 - t0
    avg_ms = (total_s / args.iters) * 1000.0

    print("\n== mpd-parser benchmark ==")
    print(f"input:  {'file ' + args.file if args.file else 'url  ' + args.url}")
    print(f"warmup: {args.warmup}")
    print(f"iters:  {args.iters}")
    print(f"reps:   {rep_count}")
    if bandwidths_sorted:
        print(f"bandwidth sample (bps): {bandwidths_sorted[:8]}")
        print(f"bandwidth max (bps):    {bandwidths_sorted[-1]}")
    else:
        print("bandwidth sample (bps): <none found>")
    print(f"total:  {total_s:.4f}s")
    print(f"avg:    {avg_ms:.3f} ms/parse\n")


if __name__ == "__main__":
    main()