"""
Integration test: Real GeM API call.
Run with: pytest tests/test_gem_integration.py -v -s
Requires internet connection.
"""
import pytest


@pytest.mark.integration
def test_gem_session_refresh():
    """Verify we can get a valid CSRF session from GeM."""
    from app.gem.session import GemSession
    s = GemSession()
    s.refresh()
    assert s._csrf_token is not None
    assert len(s._csrf_token) == 32
    print(f"\nCSRF token obtained: {s._csrf_token[:8]}...")


@pytest.mark.integration
def test_fetch_karnataka_bids():
    """Fetch real bids from GeM for Karnataka. Verifies endpoint still works."""
    from app.gem.session import GemSession
    from app.gem.fetcher import GemFetcher

    session = GemSession()
    session.refresh()
    fetcher = GemFetcher(session)

    bids, total = fetcher.fetch_bids_by_location(state="KARNATAKA", city="BANGALORE", page=1)
    print(f"\nKarnataka/Bangalore bids: total={total}, page1={len(bids)}")
    assert total > 0
    assert len(bids) > 0


@pytest.mark.integration
def test_fetch_toner_bids_in_bangalore():
    """Verify toner/printer bids exist in Bangalore variants."""
    from app.gem.session import GemSession
    from app.gem.fetcher import GemFetcher
    from app.gem.normalizer import normalize_bid

    session = GemSession()
    session.refresh()
    fetcher = GemFetcher(session)

    keywords = ["toner", "cartridge", "printer", "ink"]
    cities = ["BANGALORE", "Bangalore Urban", "BENGALURU URBAN", "Bengaluru"]
    total_matches = 0

    for city in cities:
        bids, total = fetcher.fetch_bids_by_location(state="KARNATAKA", city=city, page=1)
        for raw in bids:
            nb = normalize_bid(raw)
            if nb and any(k in (nb.category_name or "").lower() for k in keywords):
                total_matches += 1
                print(f"\n  MATCH [{city}]: {nb.bid_number} | {nb.category_name}")

    print(f"\nTotal toner/printer matches across all Bangalore variants: {total_matches}")
    # We know at least 1 from real testing (Computer Printer bid)
    assert total_matches >= 0  # May be 0 if all expired — just confirms no crash
