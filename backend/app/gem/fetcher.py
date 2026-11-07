"""
GeM BidWatch — GemFetcher
Calls GeM portal endpoints to fetch bid listings.
"""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from app.gem.session import GemSession

logger = logging.getLogger(__name__)

SEARCH_BIDS_URL = "https://bidplus.gem.gov.in/search-bids"
ALL_BIDS_URL = "https://bidplus.gem.gov.in/all-bids-data"
CITY_LIST_URL = "https://bidplus.gem.gov.in/city-list-adv"
STATE_LIST_URL = "https://bidplus.gem.gov.in/state-list-adv"


class RawBid:
    """Raw bid data as returned by GeM API."""
    def __init__(self, data: dict, state: str, city: str):
        self.raw = data
        self.state = state
        self.city = city

    def get(self, key, default=None):
        val = self.raw.get(key, default)
        # GeM wraps most values in a list
        if isinstance(val, list):
            return val[0] if val else default
        return val


class GemFetcher:
    """
    Fetches bids from GeM portal using the internal AJAX endpoints.
    Uses location-based search (consignee state + city).
    """

    def __init__(self, session: GemSession):
        self.session = session

    def fetch_bids_by_location(
        self,
        state: str,
        city: str = "",
        page: int = 1,
        bid_end_from: str = "",
        bid_end_to: str = "",
    ) -> tuple[List[RawBid], int]:
        """
        Fetch paginated bids for a state+city.
        Returns (list_of_raw_bids, total_found).
        """
        payload = {
            "searchType": "con",
            "state_name_con": state,
            "city_name_con": city,
            "bidEndFromCon": bid_end_from,
            "bidEndToCon": bid_end_to,
            "page": page,
        }

        logger.debug(f"Fetching page {page} for {state}/{city or 'all'}")
        data = self.session.post(SEARCH_BIDS_URL, payload)

        resp = data.get("response", {}).get("response", {})
        num_found = resp.get("numFound", 0)
        docs = resp.get("docs", [])

        raw_bids = [RawBid(doc, state, city) for doc in docs]
        return raw_bids, num_found

    def fetch_all_pages(
        self,
        state: str,
        city: str = "",
        max_pages: int = 5,
    ) -> List[RawBid]:
        """
        Fetch pages of bids for a state+city.
        Defaults to first 5 pages (50 most recent bids per city variant)
        to respect server rate limits during 24/7 continuous polling.
        """
        import time
        all_bids = []
        page = 1

        while page <= max_pages:
            try:
                bids, total = self.fetch_bids_by_location(state=state, city=city, page=page)
                all_bids.extend(bids)
                logger.info(f"  [{city or 'ALL'}] Page {page}: got {len(bids)} bids (total={total})")

                if not bids or len(all_bids) >= total:
                    break
                page += 1
                time.sleep(0.5)  # Polite pacing between pages
            except Exception as e:
                logger.warning(f"Error fetching page {page} for {city or 'ALL'}: {e}. Continuing with gathered bids.")
                break

        return all_bids

    def fetch_bids_by_keyword(
        self,
        keyword: str,
        page: int = 1,
    ) -> tuple[List[RawBid], int]:
        """
        Fetch paginated bids matching a search keyword via GeM all-bids-data.
        Returns (list_of_raw_bids, total_found).
        """
        payload = {
            "page": page,
            "param": {"searchBid": keyword, "searchType": "fullText"},
            "filter": {"bidStatusType": "ongoing_bids", "byType": "all", "sort": "Bid-End-Date-Oldest"},
        }
        try:
            data = self.session.post(ALL_BIDS_URL, payload)
            resp = data.get("response", {}).get("response", {})
            num_found = resp.get("numFound", 0)
            docs = resp.get("docs", [])
            raw_bids = [RawBid(doc, state="KARNATAKA", city="Bangalore Urban") for doc in docs]
            return raw_bids, num_found
        except Exception as e:
            logger.warning(f"Error fetching keyword '{keyword}' page {page}: {e}")
            return [], 0

    def get_cities_for_state(self, state: str) -> List[dict]:
        """Return list of cities for a state from GeM."""
        data = self.session.post_raw(CITY_LIST_URL, {"state_name": state})
        return data.get("data", [])
