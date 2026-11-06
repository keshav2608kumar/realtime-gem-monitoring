"""
GeM BidWatch — Live Web Dashboard
Self-contained HTML/CSS/JS responsive dashboard served by FastAPI.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GeM BidWatch — 24/7 Cloud Monitor & Alert Dashboard</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🚨</text></svg>">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @keyframes pulse-slow {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.85; transform: scale(1.02); }
    }
    .animate-pulse-slow { animation: pulse-slow 2s infinite ease-in-out; }
    @keyframes siren-glow {
      0%, 100% { box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }
      50% { box-shadow: 0 0 35px rgba(239, 68, 68, 0.9); }
    }
    .siren-active { animation: siren-glow 1s infinite alternate; }
    .glass-card {
      background: rgba(30, 41, 59, 0.7);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col font-sans antialiased selection:bg-red-500 selection:text-white">

  <!-- Top Sticky Navigation -->
  <header class="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <span class="text-2xl p-2 rounded-xl bg-red-500/20 text-red-500 border border-red-500/30">
          <i class="fa-solid fa-tower-broadcast"></i>
        </span>
        <div>
          <div class="flex items-center space-x-2">
            <h1 class="text-xl font-black tracking-tight text-white">GeM BidWatch</h1>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              24/7 Cloud Active
            </span>
          </div>
          <p class="text-xs text-slate-400 hidden sm:block">Automated Government e-Marketplace Monitoring & Emergency Alert System</p>
        </div>
      </div>

      <div class="flex items-center space-x-2 sm:space-x-3">
        <button id="btnTriggerPoll" onclick="triggerManualScan()" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition">
          <i class="fa-solid fa-arrows-rotate" id="scanIcon"></i>
          <span class="hidden sm:inline">Scan GeM Now</span>
        </button>

        <a href="https://github.com/keshav2608kumar/realtime-gem-monitoring/releases/tag/v1.0.0" target="_blank" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white shadow-lg shadow-red-900/30 flex items-center gap-1.5 transition">
          <i class="fa-brands fa-android text-base"></i>
          <span>Download APK</span>
        </a>

        <a href="/docs" target="_blank" class="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 hidden md:flex items-center gap-1 transition" title="Swagger API Documentation">
          <i class="fa-solid fa-code"></i>
          <span>API Docs</span>
        </a>
      </div>
    </div>
  </header>

  <!-- Main Content Container -->
  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">

    <!-- Hero / Summary Banner -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Card 1: System Status -->
      <div class="glass-card rounded-2xl p-4 flex items-center space-x-4">
        <div class="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 text-xl">
          <i class="fa-solid fa-shield-halved"></i>
        </div>
        <div>
          <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Engine Status</p>
          <p id="statEngineStatus" class="text-lg font-bold text-emerald-400">Online & Polling</p>
          <p id="statLastScan" class="text-xs text-slate-500">Every 5 mins (300s)</p>
        </div>
      </div>

      <!-- Card 2: Active Profile -->
      <div class="glass-card rounded-2xl p-4 flex items-center space-x-4">
        <div class="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 text-xl">
          <i class="fa-solid fa-crosshairs"></i>
        </div>
        <div>
          <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Target Location</p>
          <p id="statLocation" class="text-lg font-bold text-white">Bangalore Urban</p>
          <p class="text-xs text-slate-500">Karnataka, India</p>
        </div>
      </div>

      <!-- Card 3: Tracked Category & Keywords -->
      <div class="glass-card rounded-2xl p-4 flex items-center space-x-4">
        <div class="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 text-xl">
          <i class="fa-solid fa-tag"></i>
        </div>
        <div>
          <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Tracked Keywords</p>
          <p class="text-sm font-bold text-amber-300">toner, printer, cartridge, ink</p>
          <p class="text-xs text-slate-500">All matching products</p>
        </div>
      </div>

      <!-- Card 4: Total Alerts Fired -->
      <div class="glass-card rounded-2xl p-4 flex items-center space-x-4">
        <div class="w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 text-xl">
          <i class="fa-solid fa-bell"></i>
        </div>
        <div>
          <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Total Alerts Fired</p>
          <p id="statTotalAlerts" class="text-2xl font-black text-red-400">0</p>
          <p id="statTotalBids" class="text-xs text-slate-500">0 Total Bids In DB</p>
        </div>
      </div>
    </div>

    <!-- Quick Audio Alarm & Red Alert Test Panel -->
    <div class="rounded-2xl p-4 bg-gradient-to-r from-red-950/60 via-slate-900 to-slate-900 border border-red-900/40 flex flex-col md:flex-row items-center justify-between gap-4">
      <div class="flex items-center space-x-3 text-center md:text-left">
        <span class="text-2xl p-2.5 rounded-xl bg-red-500/20 text-red-400 border border-red-500/30">
          <i class="fa-solid fa-volume-high"></i>
        </span>
        <div>
          <h2 class="text-sm font-bold text-white">Live Web Red Alert & Loud Siren Simulator</h2>
          <p class="text-xs text-slate-400">Test how the alarm sound, flashing siren beacon, and tender payload look on both Web & Mobile.</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button onclick="testWebAlarm()" class="px-4 py-2 rounded-xl text-xs font-bold bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-900/40 flex items-center gap-2 transition">
          <i class="fa-solid fa-triangle-exclamation"></i>
          <span>Launch Red Alert Test</span>
        </button>
        <button onclick="silenceWebAlarm()" id="btnSilence" class="px-3 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 hidden transition">
          <i class="fa-solid fa-volume-xmark"></i>
          <span>Silence</span>
        </button>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="border-b border-slate-800 flex space-x-6 text-sm font-semibold">
      <button onclick="switchTab('bidsTab')" id="tabBids" class="pb-3 border-b-2 border-red-500 text-red-400 flex items-center gap-2">
        <i class="fa-solid fa-list-check"></i>
        <span>Tracked Tenders & Alerts</span>
      </button>
      <button onclick="switchTab('profilesTab')" id="tabProfiles" class="pb-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2">
        <i class="fa-solid fa-sliders"></i>
        <span>Search Profiles</span>
      </button>
      <button onclick="switchTab('appTab')" id="tabApp" class="pb-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2">
        <i class="fa-brands fa-android"></i>
        <span>Android App (APK) Setup</span>
      </button>
    </div>

    <!-- TAB 1: BIDS & ALERTS -->
    <div id="bidsTab" class="space-y-4">
      <!-- Filter & Search Toolbar -->
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="relative w-full sm:w-80">
          <i class="fa-solid fa-magnifying-glass absolute left-3 top-3 text-slate-500 text-xs"></i>
          <input type="text" id="searchInput" oninput="filterBids()" placeholder="Filter tender, category, city..." class="w-full pl-8 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition">
        </div>
        <div class="text-xs text-slate-400 flex items-center gap-2">
          <span>Auto-refreshing in <strong id="refreshTimer" class="text-slate-200">15s</strong></span>
          <button onclick="loadAllData()" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300" title="Refresh Now">
            <i class="fa-solid fa-rotate-right"></i>
          </button>
        </div>
      </div>

      <!-- Bids Table -->
      <div class="glass-card rounded-2xl overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
              <tr>
                <th class="py-3 px-4">Tender / Bid No</th>
                <th class="py-3 px-4">Item / Service Category</th>
                <th class="py-3 px-4">Delivery Location</th>
                <th class="py-3 px-4">Closing Date</th>
                <th class="py-3 px-4 text-right">Official Document</th>
              </tr>
            </thead>
            <tbody id="bidsTableBody" class="divide-y divide-slate-800/60 font-medium">
              <tr>
                <td colspan="5" class="py-12 text-center text-slate-500">
                  <i class="fa-solid fa-spinner fa-spin text-xl mb-2 text-red-500"></i>
                  <p>Loading real-time bids from GeM cloud database...</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 2: PROFILES -->
    <div id="profilesTab" class="space-y-6 hidden">
      <div class="glass-card rounded-2xl p-6">
        <h2 class="text-base font-bold text-white mb-2">Active GeM Monitoring Profiles</h2>
        <p class="text-xs text-slate-400 mb-4">The cloud scheduler queries GeM internal search endpoints 24/7 for each configured profile.</p>

        <div id="profilesList" class="space-y-4">
          <!-- Populated dynamically -->
        </div>
      </div>
    </div>

    <!-- TAB 3: ANDROID APK SETUP GUIDE -->
    <div id="appTab" class="space-y-6 hidden">
      <div class="glass-card rounded-2xl p-6 space-y-6">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h2 class="text-lg font-black text-white flex items-center gap-2">
              <i class="fa-brands fa-android text-emerald-400 text-xl"></i>
              GeM BidWatch Android App v1.0.0
            </h2>
            <p class="text-xs text-slate-400 mt-1">Get instant loud alarm sirens and full-screen red alerts even when phone is locked or screen is off.</p>
          </div>
          <a href="https://github.com/keshav2608kumar/realtime-gem-monitoring/releases/download/v1.0.0/GeM_BidWatch.apk" class="px-5 py-2.5 rounded-xl text-sm font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/30 flex items-center gap-2 transition">
            <i class="fa-solid fa-download"></i>
            <span>Download APK (Release v1.0.0)</span>
          </a>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
            <span class="w-7 h-7 rounded-full bg-red-500/20 text-red-400 font-bold flex items-center justify-center text-xs mb-3">1</span>
            <h3 class="text-sm font-bold text-white mb-1">Install APK</h3>
            <p class="text-xs text-slate-400">Download <code class="text-amber-300">GeM_BidWatch.apk</code> on your Android phone and tap Install. Allow "Install unknown apps" if prompted.</p>
          </div>

          <div class="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
            <span class="w-7 h-7 rounded-full bg-red-500/20 text-red-400 font-bold flex items-center justify-center text-xs mb-3">2</span>
            <h3 class="text-sm font-bold text-white mb-1">Pre-Configured URL</h3>
            <p class="text-xs text-slate-400">The app automatically connects to this cloud instance (<code class="text-sky-300 font-mono text-[11px]">https://realtime-gem-monitoring.onrender.com</code>). Zero setup required.</p>
          </div>

          <div class="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
            <span class="w-7 h-7 rounded-full bg-red-500/20 text-red-400 font-bold flex items-center justify-center text-xs mb-3">3</span>
            <h3 class="text-sm font-bold text-white mb-1">Battery Unrestricted</h3>
            <p class="text-xs text-slate-400">Go to Android Settings &gt; Apps &gt; GeM BidWatch &gt; Battery &gt; Set to <strong>"Unrestricted"</strong> so alarms ring even when locked.</p>
          </div>
        </div>
      </div>
    </div>

  </main>

  <!-- Footer -->
  <footer class="border-t border-slate-800 bg-slate-950 py-4 text-center text-xs text-slate-500">
    <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
      <p>GeM BidWatch — Continuous 24/7 Monitoring Engine for Government e-Marketplace (GeM India)</p>
      <p class="font-mono text-slate-600">v1.0.0 • 100% Free Tier Cloud Hosted</p>
    </div>
  </footer>

  <!-- FULL SCREEN RED ALERT MODAL (SIMULATOR) -->
  <div id="redAlertModal" class="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 hidden">
    <div class="max-w-md w-full bg-gradient-to-b from-red-950 to-slate-950 border-2 border-red-500 rounded-3xl p-6 shadow-2xl shadow-red-900/50 space-y-5 text-center relative overflow-hidden">

      <!-- Flashing Beacon Icon -->
      <div class="inline-block p-4 rounded-full bg-red-500/30 text-red-500 border border-red-500 animate-pulse-slow">
        <i class="fa-solid fa-triangle-exclamation text-4xl"></i>
      </div>

      <div>
        <span class="px-3 py-1 rounded-full text-xs font-black tracking-widest bg-red-600 text-white uppercase animate-pulse">EMERGENCY GeM ALERT</span>
        <h3 class="text-2xl font-black text-white mt-2">MATCHING TENDER DETECTED!</h3>
        <p id="modalLocation" class="text-xs text-slate-300 font-semibold mt-1">Bangalore Urban, KARNATAKA</p>
      </div>

      <!-- Tender Card Info -->
      <div class="bg-slate-900/90 rounded-2xl p-4 text-left border border-red-900/40 space-y-3">
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Tender / Bid Number</span>
          <p id="modalBidNo" class="text-lg font-black text-white font-mono">GEM/2026/B/8123875</p>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Matched Keywords</span>
          <p id="modalKeywords" class="text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-md inline-block">printer, cartridge, toner</p>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Category Name</span>
          <p id="modalCategory" class="text-sm font-semibold text-slate-200">Computer Printer (V2) / Toner Cartridge</p>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Delivery Location</span>
          <p id="modalDelivery" class="text-xs font-semibold text-slate-300 flex items-center gap-1">
            <i class="fa-solid fa-location-dot text-red-400"></i>
            <span>Bangalore Urban, KARNATAKA</span>
          </p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="space-y-2 pt-2">
        <a id="modalDocLink" href="https://bidplus.gem.gov.in/showbidDocument/9993172" target="_blank" class="w-full py-3 rounded-xl text-sm font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/50 transition">
          <i class="fa-solid fa-file-pdf text-base"></i>
          <span>Open Official GeM Bid PDF</span>
        </a>
        <button onclick="silenceWebAlarm()" class="w-full py-2.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition">
          <i class="fa-solid fa-volume-xmark mr-1"></i> Silence Alarm & Close
        </button>
      </div>
    </div>
  </div>

  <!-- Client-side Logic -->
  <script>
    let allBids = [];
    let audioCtx = null;
    let alarmOsc = null;
    let alarmGain = null;
    let sirenInterval = null;
    let timerCount = 15;

    // ─── TABS ────────────────────────────────────────────────────────────────
    function switchTab(tabId) {
      document.getElementById('bidsTab').classList.add('hidden');
      document.getElementById('profilesTab').classList.add('hidden');
      document.getElementById('appTab').classList.add('hidden');

      document.getElementById('tabBids').className = "pb-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2";
      document.getElementById('tabProfiles').className = "pb-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2";
      document.getElementById('tabApp').className = "pb-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2";

      document.getElementById(tabId).classList.remove('hidden');
      if (tabId === 'bidsTab') document.getElementById('tabBids').className = "pb-3 border-b-2 border-red-500 text-red-400 flex items-center gap-2";
      if (tabId === 'profilesTab') document.getElementById('tabProfiles').className = "pb-3 border-b-2 border-red-500 text-red-400 flex items-center gap-2";
      if (tabId === 'appTab') document.getElementById('tabApp').className = "pb-3 border-b-2 border-red-500 text-red-400 flex items-center gap-2";
    }

    // ─── DATA FETCHING ───────────────────────────────────────────────────────
    async function loadAllData() {
      try {
        // 1. Fetch Health
        const hRes = await fetch('/health/');
        if (hRes.ok) {
          const h = await hRes.json();
          document.getElementById('statEngineStatus').textContent = h.monitor_running ? 'Online & Polling' : 'Paused';
          document.getElementById('statTotalBids').textContent = `${h.total_bids_in_db || 0} Total Bids In DB`;
        }

        // 2. Fetch Profiles
        const pRes = await fetch('/profiles/');
        if (pRes.ok) {
          const profiles = await pRes.json();
          renderProfiles(profiles);
        }

        // 3. Fetch Alerts
        const aRes = await fetch('/alerts/?limit=100');
        if (aRes.ok) {
          const alerts = await aRes.json();
          document.getElementById('statTotalAlerts').textContent = alerts.length;
        }

        // 4. Fetch Bids
        const bRes = await fetch('/bids/?limit=100');
        if (bRes.ok) {
          allBids = await bRes.json();
          renderBids(allBids);
        }
      } catch (e) {
        console.error("Fetch error:", e);
      }
    }

    function renderBids(bids) {
      const tbody = document.getElementById('bidsTableBody');
      if (!bids || bids.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" class="py-12 text-center text-slate-500">
              <i class="fa-solid fa-inbox text-3xl mb-2 text-slate-600 block"></i>
              <p class="font-semibold text-slate-300">No Bids Stored Yet</p>
              <p class="text-xs text-slate-500 mt-1">The poller is monitoring Bangalore Urban for toner/cartridge/printer. Click "Scan GeM Now" to trigger a run immediately.</p>
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = bids.map(b => `
        <tr class="hover:bg-slate-800/40 transition">
          <td class="py-3 px-4 font-mono font-bold text-white whitespace-nowrap">
            ${b.bid_number}
          </td>
          <td class="py-3 px-4 text-slate-200">
            <div class="line-clamp-2 max-w-md font-semibold">${escapeHtml(b.category_name)}</div>
          </td>
          <td class="py-3 px-4 text-slate-300 whitespace-nowrap">
            <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-slate-800 text-slate-300">
              <i class="fa-solid fa-location-dot text-red-400 text-[10px]"></i>
              ${escapeHtml(b.consignee_city || 'Bangalore')}, ${escapeHtml(b.consignee_state || 'KARNATAKA')}
            </span>
          </td>
          <td class="py-3 px-4 text-slate-400 whitespace-nowrap">
            ${b.end_date ? new Date(b.end_date).toLocaleDateString() : 'N/A'}
          </td>
          <td class="py-3 px-4 text-right whitespace-nowrap">
            <a href="${b.bid_url}" target="_blank" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition">
              <i class="fa-solid fa-file-pdf"></i>
              <span>View PDF</span>
            </a>
          </td>
        </tr>
      `).join('');
    }

    function renderProfiles(profiles) {
      const container = document.getElementById('profilesList');
      if (!profiles || profiles.length === 0) {
        container.innerHTML = `<p class="text-slate-500 text-xs">No active profiles found.</p>`;
        return;
      }
      container.innerHTML = profiles.map(p => `
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <h4 class="text-sm font-bold text-white">${escapeHtml(p.name)}</h4>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${p.is_active ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-slate-700 text-slate-400'}">
                ${p.is_active ? 'ACTIVE' : 'PAUSED'}
              </span>
            </div>
            <p class="text-xs text-slate-400">
              <strong>State:</strong> ${p.state} &bull; <strong>Cities:</strong> ${p.cities.join(', ')}
            </p>
            <div class="flex flex-wrap gap-1 mt-2">
              ${p.keywords.map(k => `<span class="px-2 py-0.5 rounded-md text-[11px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">${k}</span>`).join('')}
            </div>
          </div>
          <div class="text-xs text-slate-400">
            <span>Interval: <strong>${p.poll_interval_seconds}s</strong></span>
          </div>
        </div>
      `).join('');
    }

    function filterBids() {
      const q = document.getElementById('searchInput').value.toLowerCase().trim();
      if (!q) {
        renderBids(allBids);
        return;
      }
      const filtered = allBids.filter(b => 
        (b.bid_number && b.bid_number.toLowerCase().includes(q)) ||
        (b.category_name && b.category_name.toLowerCase().includes(q)) ||
        (b.consignee_city && b.consignee_city.toLowerCase().includes(q))
      );
      renderBids(filtered);
    }

    async function triggerManualScan() {
      const icon = document.getElementById('scanIcon');
      icon.classList.add('fa-spin');
      try {
        const res = await fetch('/health/trigger-poll', { method: 'POST' });
        if (res.ok) {
          setTimeout(loadAllData, 2000);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setTimeout(() => icon.classList.remove('fa-spin'), 1500);
      }
    }

    // ─── WEB AUDIO ALARM SYNTHESIZER ─────────────────────────────────────────
    function testWebAlarm() {
      document.getElementById('redAlertModal').classList.remove('hidden');
      document.getElementById('btnSilence').classList.remove('hidden');

      try {
        if (!audioCtx) {
          audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
          audioCtx.resume();
        }

        if (alarmOsc) {
          alarmOsc.stop();
          alarmOsc.disconnect();
        }

        alarmOsc = audioCtx.createOscillator();
        alarmGain = audioCtx.createGain();

        alarmOsc.type = 'sawtooth';
        alarmGain.gain.setValueAtTime(0.3, audioCtx.currentTime);

        alarmOsc.connect(alarmGain);
        alarmGain.connect(audioCtx.destination);
        alarmOsc.start();

        let high = false;
        clearInterval(sirenInterval);
        sirenInterval = setInterval(() => {
          if (!audioCtx) return;
          const targetFreq = high ? 960 : 700;
          alarmOsc.frequency.exponentialRampToValueAtTime(targetFreq, audioCtx.currentTime + 0.15);
          high = !high;
        }, 250);
      } catch (e) {
        console.warn("Audio Context error:", e);
      }
    }

    function silenceWebAlarm() {
      document.getElementById('redAlertModal').classList.add('hidden');
      document.getElementById('btnSilence').classList.add('hidden');
      clearInterval(sirenInterval);
      if (alarmGain && audioCtx) {
        try {
          alarmGain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.1);
          setTimeout(() => {
            if (alarmOsc) {
              alarmOsc.stop();
              alarmOsc.disconnect();
              alarmOsc = null;
            }
          }, 150);
        } catch (_) {}
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    // Auto-refresh timer
    setInterval(() => {
      timerCount--;
      if (timerCount <= 0) {
        timerCount = 15;
        loadAllData();
      }
      document.getElementById('refreshTimer').textContent = `${timerCount}s`;
    }, 1000);

    // Initial Load
    loadAllData();
  </script>
</body>
</html>
"""
