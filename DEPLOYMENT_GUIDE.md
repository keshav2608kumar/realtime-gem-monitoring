# 🛡️ GeM BidWatch — Production Deployment & Operation Guide

This guide explains how to operate **GeM BidWatch** 24/7 on a cloud server so you never need to keep your laptop on, and how to receive loud alarm-style alerts on your Android device.

---

## 🏗️ Architecture Summary

1. **Cloud Monitoring Engine (Python 3 + FastAPI + APScheduler)**:
   - Polls `bidplus.gem.gov.in/search-bids` every 5 minutes.
   - Monitors Bangalore (`BANGALORE`, `Bangalore Urban`, `BENGALURU URBAN`, `Bengaluru`).
   - Filters on your keywords (`toner`, `cartridge`, `printer`, `ink`).
   - Deduplicates bids using GeM Bid IDs (no duplicate alerts).
   - Records all alerts and scans in the database.
   - Dispatches instant high-priority FCM push notifications to your Android phone.

2. **Android Application (Flutter + Android Native)**:
   - Registers for high-priority FCM push notifications.
   - Background handler awakens the device even when the app is in background or closed.
   - Rings continuous loud alarm sound and strong vibration pattern until acknowledged.
   - Full-screen Red Alert UI with one-tap link to the official GeM bid document PDF.

---

## ☁️ Step 1: 24/7 Free Cloud Server Setup

### Recommended: Oracle Cloud Always Free (100% Free Forever)
Oracle Cloud offers an Always Free ARM/x86 VM with 24GB RAM and public IP. It never sleeps.

1. Sign up at [cloud.oracle.com](https://cloud.oracle.com/) (select "Always Free").
2. Create an **Ubuntu 24.04** compute instance.
3. SSH into your VM:
   ```bash
   ssh -i your-key.key ubuntu@<YOUR_VM_PUBLIC_IP>
   ```
4. Install Python and Git:
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv git
   ```
5. Clone or copy `gem_bidwatch/backend` to the server:
   ```bash
   cd ~
   git clone <YOUR_REPO> gem_bidwatch || scp -r gem_bidwatch ubuntu@<IP>:~/
   cd gem_bidwatch/backend
   ```
6. Create virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
7. Configure `systemd` for auto-restart on boot/crashes:
   ```bash
   sudo cp gem_bidwatch.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable gem_bidwatch
   sudo systemctl start gem_bidwatch
   ```
8. Verify status:
   ```bash
   sudo systemctl status gem_bidwatch
   curl http://localhost:8000/health/
   ```

---

## 🔥 Step 2: Firebase Cloud Messaging (FCM) Setup (Free)

To receive push notifications remotely:
1. Go to [Firebase Console](https://console.firebase.google.com/) and create a project (e.g. `gem-bidwatch`).
2. Go to **Project Settings > Service accounts > Generate new private key**.
3. Download the JSON file, name it `firebase_service_account.json`, and place it in `gem_bidwatch/backend/`.
4. In `.env`, set:
   ```env
   FIREBASE_SERVICE_ACCOUNT_PATH=./firebase_service_account.json
   ```
5. In Firebase Console, add an **Android App** with package name `com.gembidwatch.app`.
6. Download `google-services.json` and place it in `gem_bidwatch/android_app/android/app/`.

---

## 📱 Step 3: Android App Setup & Battery Configuration

### Building the APK
From your machine:
```bash
cd gem_bidwatch/android_app
flutter pub get
flutter build apk --release
```
The output file will be in `build/app/outputs/flutter-apk/app-release.apk`.
Transfer and install it on your Android phone.

### Configuring App on Your Phone:
1. Open **GeM BidWatch**.
2. Go to **Settings**:
   - Set **Cloud Backend API URL** to `http://<YOUR_SERVER_IP>:8000`.
   - Tap **Save & Test Connection**.
   - Tap **Test Alarm Sound** to verify speaker volume and vibration.

### ⚠️ Crucial Android Battery Optimization Settings:
Android battery savers kill background apps unless exempted:
1. On your phone: Open **Settings > Apps > GeM BidWatch**.
2. Select **Battery** > Set to **"Unrestricted"** (or "No restrictions").
3. On Xiaomi/Redmi/Poco: Enable **"Auto-start"**.
4. On Vivo/Oppo/Realme: Enable **"Allow background activity"** and **"High background power consumption"**.

---

## 📊 Step 4: Verification & Monitoring Dashboard

You can view the real-time status of your monitoring worker at any time:
- Web dashboard/API health: `http://<YOUR_SERVER_IP>:8000/health/`
- View all alerts: `http://<YOUR_SERVER_IP>:8000/alerts/`
- Trigger immediate scan: `POST http://<YOUR_SERVER_IP>:8000/health/trigger-poll`
- Interactive Swagger docs: `http://<YOUR_SERVER_IP>:8000/docs`
