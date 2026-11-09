# GeM BidWatch — Cloud Scanner Deployment Guide

This guide describes how to deploy the 24/7 autonomous GeM Cloud Scanner worker in an Indian Cloud Region without running any local scripts or keeping a personal laptop turned on.

All configuration files and handlers are located in the `cloud_scanner/` directory.

---

## Deployment Option 1: AWS Mumbai (`ap-south-1`) via AWS Lambda (Recommended - 100% Free Forever)

### Prerequisites
- AWS Account (Free Tier).
- AWS CLI or AWS SAM CLI installed.

### 1-Click Deployment Steps
1. Navigate to the cloud scanner folder:
   ```bash
   cd cloud_scanner
   ```
2. Build the package:
   ```bash
   sam build
   ```
3. Deploy to AWS Mumbai:
   ```bash
   sam deploy --guided
   ```
   - **Stack Name:** `gem-bidwatch-scanner`
   - **AWS Region:** `ap-south-1` (Mumbai)
   - **Parameter BACKEND_SYNC_URL:** `https://realtime-gem-monitoring.onrender.com/bids/batch-sync`
   - **Parameter SCANNER_SECRET:** `gem_bidwatch_cloud_token_v1`
4. Confirm deployment:
   The AWS SAM template automatically provisions an EventBridge Rule running every 5 minutes (`rate(5 minutes)`) that triggers `lambda_function.py`.

---

## Deployment Option 2: Google Cloud Functions in Mumbai (`asia-south1`) (100% Free Forever)

### 1-Click Deployment via gcloud CLI
```bash
cd cloud_scanner

gcloud functions deploy gem-cloud-scanner \
    --gen2 \
    --runtime=python312 \
    --region=asia-south1 \
    --source=. \
    --entry-point=gem_scanner_http \
    --trigger-http \
    --set-env-vars BACKEND_SYNC_URL=https://realtime-gem-monitoring.onrender.com/bids/batch-sync,SCANNER_SECRET=gem_bidwatch_cloud_token_v1
```

Set up Cloud Scheduler to trigger every 5 minutes:
```bash
gcloud scheduler jobs create http gem-5min-cron \
    --location=asia-south1 \
    --schedule="*/5 * * * *" \
    --uri="https://asia-south1-YOUR_PROJECT.cloudfunctions.net/gem-cloud-scanner" \
    --http-method=GET
```

---

## Deployment Option 3: Fly.io Mumbai (`bom`) Container

```bash
cd cloud_scanner
fly launch --region bom --name gem-cloud-scanner
fly deploy
```

---

## Deployment Option 4: Dedicated Linux VM in India (Oracle Always Free / EC2)

1. SSH into the Indian Ubuntu VM.
2. Clone repository or copy `cloud_scanner/` and `backend/`.
3. Install dependencies:
   ```bash
   pip3 install -r cloud_scanner/requirements.txt
   ```
4. Copy systemd service:
   ```bash
   sudo cp cloud_scanner/systemd/gem_scanner.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now gem_scanner.service
   ```
5. Monitor logs:
   ```bash
   journalctl -u gem_scanner.service -f
   ```
