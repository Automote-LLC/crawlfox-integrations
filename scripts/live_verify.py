#!/usr/bin/env python3
"""Live verification for crawlfox-py against production API."""
from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime, timezone

from crawlfox import AsyncCrawlFox, CrawlFox, CrawlFoxError


def banner(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def ok(label: str, detail: str = "") -> None:
    msg = f"  ✓ {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def fail(label: str, err: Exception) -> None:
    print(f"  ✗ {label} — {type(err).__name__}: {err}")


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    passed = 0
    failed = 0

    banner(f"crawlfox-py live verify @ {stamp}")
    app = CrawlFox()  # CRAWLFOX_API_KEY from env
    print(f"  API base: {app.api_url}")

    # 1. Sync scrape — example.com
    banner("1. Sync scrape — example.com")
    url = f"https://example.com/?sdk-live={stamp}"
    try:
        t0 = time.perf_counter()
        doc = app.scrape(url, formats=["markdown", "links"])
        elapsed = time.perf_counter() - t0
        md_len = len(doc.markdown or "")
        links = len(doc.links or [])
        meta = doc.metadata
        ok(
            "scrape",
            f"{elapsed:.2f}s | markdown={md_len} chars | links={links} | "
            f"status={meta.status_code if meta else '?'} | "
            f"source={meta.source_url if meta else '?'}",
        )
        print(f"  preview: {(doc.markdown or '')[:120]!r}...")
        passed += 1
    except CrawlFoxError as e:
        fail("scrape", e)
        failed += 1

    # 2. Sync scrape — nike.com (hard site)
    banner("2. Sync scrape — nike.com (hard site)")
    try:
        t0 = time.perf_counter()
        doc = app.scrape("https://www.nike.com/", formats=["markdown"])
        elapsed = time.perf_counter() - t0
        md_len = len(doc.markdown or "")
        meta = doc.metadata
        ok(
            "scrape nike.com",
            f"{elapsed:.2f}s | markdown={md_len} chars | "
            f"status={meta.status_code if meta else '?'}",
        )
        print(f"  preview: {(doc.markdown or '')[:200]!r}...")
        passed += 1
    except CrawlFoxError as e:
        fail("scrape nike.com", e)
        failed += 1

    # 3. Search — Google
    banner("3. Search — Google")
    try:
        t0 = time.perf_counter()
        serp = app.search("crawlfox web scraping api", engine="google", num=3)
        elapsed = time.perf_counter() - t0
        hits = serp.web or []
        ok("google search", f"{elapsed:.2f}s | {len(hits)} results")
        for h in hits[:3]:
            print(f"    #{h.position} {h.title[:60] if h.title else '?'} → {h.url}")
        passed += 1
    except CrawlFoxError as e:
        fail("google search", e)
        failed += 1

    # 4. Batch scrape
    banner("4. Batch scrape — example.org + example.net")
    try:
        t0 = time.perf_counter()
        batch = app.batch(
            ["https://example.org/", "https://example.net/"],
            formats=["markdown"],
        )
        elapsed = time.perf_counter() - t0
        docs = batch.data or []
        ok(
            "batch",
            f"{elapsed:.2f}s | {len(docs)} docs | "
            + ", ".join(f"md={len(d.markdown or '')}" for d in docs),
        )
        passed += 1
    except CrawlFoxError as e:
        fail("batch", e)
        failed += 1

    # 5. Async scrape + search
    banner("5. Async scrape + search")
    async def async_tests() -> tuple[int, int]:
        p, f = 0, 0
        async with AsyncCrawlFox() as async_app:
            try:
                t0 = time.perf_counter()
                doc = await async_app.scrape(
                    "https://example.com/", formats=["markdown"]
                )
                elapsed = time.perf_counter() - t0
                ok(
                    "async scrape",
                    f"{elapsed:.2f}s | markdown={len(doc.markdown or '')} chars",
                )
                p += 1
            except CrawlFoxError as e:
                fail("async scrape", e)
                f += 1

            try:
                t0 = time.perf_counter()
                serp = await async_app.search("example domain", engine="bing", num=2)
                elapsed = time.perf_counter() - t0
                ok(
                    "async bing search",
                    f"{elapsed:.2f}s | {len(serp.web or [])} results",
                )
                p += 1
            except CrawlFoxError as e:
                fail("async bing search", e)
                f += 1
        return p, f

    ap, af = asyncio.run(async_tests())
    passed += ap
    failed += af

    banner(f"SUMMARY: {passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
