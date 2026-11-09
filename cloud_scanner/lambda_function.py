"""
GeM BidWatch — AWS Lambda Serverless Cloud Scanner
Region: AWS Mumbai (ap-south-1)
Trigger: Amazon EventBridge Rule (Rate: 5 minutes)
Monthly Cost: $0.00 (within 1,000,000 free Lambda invocations/month).
"""

import json
import logging
from cloud_scanner import GemSession, GemFetcher, run_single_scan_cycle

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global session reuse across warm Lambda container invocations
_cached_session = None
_cached_fetcher = None


def get_gem_client():
    global _cached_session, _cached_fetcher
    if _cached_session is None:
        _cached_session = GemSession()
        _cached_fetcher = GemFetcher(_cached_session)
    return _cached_session, _cached_fetcher


def lambda_handler(event, context):
    """
    AWS Lambda entrypoint triggered periodically by EventBridge cron.
    Executes a complete scan across Complete Bengaluru Region and syncs to Render.
    """
    logger.info("⚡ AWS Lambda GeM Cloud Scanner triggered in region: ap-south-1 (Mumbai)")
    session, fetcher = get_gem_client()

    try:
        result = run_single_scan_cycle(session, fetcher)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "GeM scan and sync completed successfully from AWS Mumbai",
                "result": result
            })
        }
    except Exception as e:
        logger.error(f"Lambda execution error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
