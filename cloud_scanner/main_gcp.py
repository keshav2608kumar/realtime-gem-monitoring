"""
GeM BidWatch — Google Cloud Functions (2nd Gen) Cloud Scanner
Region: GCP Mumbai (asia-south1)
Trigger: Cloud Scheduler (cron: */5 * * * *)
Cost: $0.00 (within 2,000,000 free invocations/month).
"""

import json
import functions_framework
from cloud_scanner import GemSession, GemFetcher, run_single_scan_cycle

_session = None
_fetcher = None


def get_client():
    global _session, _fetcher
    if _session is None:
        _session = GemSession()
        _fetcher = GemFetcher(_session)
    return _session, _fetcher


@functions_framework.http
def gem_scanner_http(request):
    session, fetcher = get_client()
    try:
        result = run_single_scan_cycle(session, fetcher)
        return (json.dumps({"status": "success", "result": result}), 200, {"Content-Type": "application/json"})
    except Exception as e:
        return (json.dumps({"status": "error", "message": str(e)}), 500, {"Content-Type": "application/json"})
