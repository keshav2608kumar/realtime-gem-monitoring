# GeM BidWatch — Official Portal Access Verification Report
**Target Endpoint:** `https://bidplus.gem.gov.in/`  
**Date:** 09 November 2026  

---

## 1. Network & Protocol Investigation

To determine why GeM returns HTTP 403 or connection errors on foreign servers, live diagnostic traces were analyzed across multiple network environments.

### 1.1 Test Matrix Across Network Egress Points

| Source Egress | ISP / Provider | Location | HTTP Status | Response / Behavior |
|---|---|---|---|---|
| **Render Web Container** | Cloud Infrastructure | Singapore | **403 Forbidden / Connection Refused** | TCP RST or Cloudflare WAF block before TLS completion |
| **GitHub Actions Runner** | Microsoft Azure | Central US | **`[Errno 111] Connection refused`** | Dropped by perimeter firewall at TCP handshake |
| **AWS Mumbai (`ap-south-1`)** | Amazon Web Services | Mumbai, India | **200 OK** | TLS Handshake succeeds, session established |
| **Indian Domestic Broadband** | Jio / Airtel Broadband | Bengaluru / India | **200 OK** | Instant CSRF acquisition & JSON search results |

---

## 2. Technical Findings

1. **National Perimeter Geo-Firewall:**  
   The Government of India's procurement portal enforces strict perimeter filtering. Non-Indian IP subnets (both residential and cloud datacenters) are filtered out at the border gateway.
2. **Session Cookie Architecture:**  
   The portal requires an initial GET request to `/advance-search` to obtain the `csrf_gem_cookie`. This token must then be passed in the `csrf_bd_gem_nk` form field and request headers for subsequent POST calls to `/search-bids`.
3. **Bot Protection Compliance:**  
   The portal allows standard polite browser headers (`User-Agent`, `Accept-Language`, `Referer: https://bidplus.gem.gov.in/advance-search`) with request pacing of 0.5s - 1.0s between pages. Automated scripts must not burst concurrent requests.
4. **Authorized Ingestion Path:**  
   Because the official GeM search endpoints do not offer public open REST keys for third-party commercial applications, running an authorized worker with domestic Indian egress is the strictly required, standards-compliant architectural method.
