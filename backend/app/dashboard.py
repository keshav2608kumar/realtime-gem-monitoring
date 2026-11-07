"""
GeM BidWatch — Executive Enterprise Dashboard
Real-time 24/7 Procurement Monitoring with Accurate Administrative Locations,
Timezone-Aware IST Timestamps, Strict Lifecycle Segregation, and Vector Branding.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Dashboard"])

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GeM BidWatch — Enterprise Procurement Radar</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'><path d='M24 4L8 10V22C8 31.5 14.8 40.3 24 43C33.2 40.3 40 31.5 40 22V10L24 4Z' fill='%230B132B' stroke='%233B82F6' stroke-width='2.2'/><circle cx='24' cy='11' r='4' fill='%23EF4444'/></svg>">
  
  <!-- Tailwind CSS & FontAwesome -->
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  
  <!-- Inter & JetBrains Mono Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap" rel="stylesheet">
  
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['Inter', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
          },
          colors: {
            brand: {
              50: '#eff6ff',
              500: '#3b82f6',
              600: '#2563eb',
              900: '#1e3a8a',
            }
          }
        }
      }
    }
  </script>
  <style>
    body { font-feature-settings: "cv02", "cv03", "cv04", "cv11"; }
    @keyframes pulseRadar {
      0% { transform: scale(0.95); opacity: 0.8; }
      50% { transform: scale(1.15); opacity: 1; filter: drop-shadow(0 0 10px rgba(239, 68, 68, 0.7)); }
      100% { transform: scale(0.95); opacity: 0.8; }
    }
    .radar-pulse { animation: pulseRadar 2s infinite ease-in-out; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased selection:bg-red-500 selection:text-white">

  <!-- TOP EXECUTIVE NAVBAR -->
  <header class="border-b border-slate-800/80 bg-slate-900/95 sticky top-0 z-40 backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      
      <!-- Logo & System Identity -->
      <div class="flex items-center gap-3.5">
        <div class="w-10 h-10 rounded-xl bg-slate-950 border border-blue-500/30 flex items-center justify-center shadow-lg shadow-blue-500/10">
          <svg class="w-7 h-7" viewBox="0 0 48 48" fill="none">
            <path d="M24 4L8 10V22C8 31.5 14.8 40.3 24 43C33.2 40.3 40 31.5 40 22V10L24 4Z" fill="#0B132B" stroke="#3B82F6" stroke-width="2.5" stroke-linejoin="round"/>
            <path d="M14 22C17 18 20.5 16 24 16C27.5 16 31 18 34 22" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round"/>
            <rect x="18" y="21" width="12" height="15" rx="1.5" fill="#1E293B" stroke="#F8FAFC" stroke-width="1.8"/>
            <line x1="21" y1="25" x2="27" y2="25" stroke="#94A3B8" stroke-width="1.5" stroke-linecap="round"/>
            <line x1="21" y1="29" x2="27" y2="29" stroke="#94A3B8" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="24" cy="10" r="3.2" fill="#EF4444" class="radar-pulse"/>
          </svg>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="font-extrabold text-base sm:text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">GeM BidWatch</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">PRO v2.0</span>
          </div>
          <p class="text-[11px] text-slate-400 hidden sm:block">Government e-Marketplace Enterprise Procurement Radar</p>
        </div>
      </div>

      <!-- Controls & Siren Toggle -->
      <div class="flex items-center gap-3">
        <!-- Live Countdown -->
        <div class="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-400">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
          <span>Next Scan: <strong id="refreshTimer" class="text-slate-200 font-mono">15s</strong></span>
        </div>

        <!-- Audio Siren Toggle -->
        <button id="btnAlarmToggle" onclick="toggleAudioAlarm()" class="px-3 py-1.5 rounded-lg text-xs font-bold border transition flex items-center gap-2 bg-red-950/40 text-red-400 border-red-500/30 hover:bg-red-900/50">
          <i id="alarmIcon" class="fa-solid fa-volume-high"></i>
          <span id="alarmText" class="hidden sm:inline">Siren: ON</span>
        </button>

        <!-- Refresh Button -->
        <button onclick="triggerImmediateRefresh()" title="Trigger GeM Poller" class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition">
          <i id="refreshIcon" class="fa-solid fa-arrows-rotate text-xs"></i>
        </button>

        <!-- Android APK Download Link -->
        <a href="https://github.com/keshav2608kumar/realtime-gem-monitoring/releases/download/v1.0.0/GeM_BidWatch.apk" target="_blank" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white flex items-center gap-1.5 shadow-md shadow-blue-600/30 transition">
          <i class="fa-brands fa-android text-sm"></i>
          <span class="hidden sm:inline">Get APK</span>
        </a>
      </div>

    </div>
  </header>

  <!-- MAIN DASHBOARD CONTENT -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full space-y-6">

    <!-- METRIC METADATA CARDS -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      
      <!-- Metric 1: System Status -->
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm flex items-center justify-between">
        <div>
          <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Engine Status</p>
          <p id="statHealth" class="text-base sm:text-lg font-black text-emerald-400 mt-1 flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>24/7 Monitoring</span>
          </p>
          <p id="statHealthSubtitle" class="text-[10px] text-slate-500 mt-0.5">Continuous 300s Polling</p>
        </div>
        <div class="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
          <i class="fa-solid fa-server"></i>
        </div>
      </div>

      <!-- Metric 2: Active Tenders in DB -->
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm flex items-center justify-between">
        <div>
          <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Active Bids in DB</p>
          <p id="statActiveBids" class="text-base sm:text-lg font-black text-white font-mono mt-1">-- Active</p>
          <p id="statTotalBids" class="text-[10px] text-slate-500 mt-0.5">-- Total Tracked</p>
        </div>
        <div class="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
          <i class="fa-solid fa-file-invoice"></i>
        </div>
      </div>

      <!-- Metric 3: Fired Alerts (Accurate Persisted DB Count) -->
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm flex items-center justify-between">
        <div>
          <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Fired Alerts</p>
          <p id="statAlerts" class="text-base sm:text-lg font-black text-red-400 font-mono mt-1">-- Alerts</p>
          <p id="statUnackAlerts" class="text-[10px] text-red-400/80 mt-0.5">-- Pending Action</p>
        </div>
        <div class="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
          <i class="fa-solid fa-bell"></i>
        </div>
      </div>

      <!-- Metric 4: Expired Tenders -->
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm flex items-center justify-between">
        <div>
          <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Expired Bids</p>
          <p id="statExpiredBids" class="text-base sm:text-lg font-black text-slate-400 font-mono mt-1">-- Expired</p>
          <p class="text-[10px] text-slate-500 mt-0.5">Excluded from Active Feed</p>
        </div>
        <div class="w-10 h-10 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400">
          <i class="fa-solid fa-calendar-xmark"></i>
        </div>
      </div>

    </div>

    <!-- ACTIVE EMERGENCY BANNER -->
    <div id="activeAlertBanner" class="hidden p-4 rounded-xl bg-gradient-to-r from-red-950/80 via-slate-900 to-slate-900 border-l-4 border-l-red-500 border border-red-900/40 shadow-lg">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div class="flex items-start gap-3">
          <div class="w-9 h-9 rounded-lg bg-red-600/20 border border-red-500/40 flex items-center justify-center text-red-400 flex-shrink-0 mt-0.5">
            <i class="fa-solid fa-triangle-exclamation text-base"></i>
          </div>
          <div>
            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-red-600 text-white">LATEST MATCH</span>
              <span id="bannerTenderNo" class="font-mono font-bold text-sm text-white">--</span>
              <span id="bannerLocation" class="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-300">--</span>
              <span id="bannerStatus" class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300">ACTIVE</span>
            </div>
            <p id="bannerDept" class="text-xs font-semibold text-slate-200 mt-1">--</p>
            <p id="bannerCat" class="text-xs text-slate-400 mt-0.5 line-clamp-1">--</p>
          </div>
        </div>
        <div class="flex items-center gap-2 self-end sm:self-center">
          <div class="text-right mr-2 hidden md:block">
            <p class="text-[10px] uppercase font-bold text-slate-400">Deadline (IST)</p>
            <p id="bannerDeadline" class="text-xs font-mono font-bold text-amber-300">--</p>
          </div>
          <button id="btnBannerAck" onclick="ackCurrentBannerAlert()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 border border-slate-700 flex items-center gap-1.5">
            <i class="fa-solid fa-check"></i>
            <span>Acknowledge</span>
          </button>
          <a id="bannerDocLink" href="#" target="_blank" class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-xs font-bold text-white shadow-md shadow-red-600/30 flex items-center gap-1.5">
            <i class="fa-solid fa-file-pdf"></i>
            <span>View GeM PDF</span>
          </a>
        </div>
      </div>
    </div>

    <!-- TENDER FEED CONTROLS & TABLE -->
    <div class="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl overflow-hidden">
      
      <!-- CONTROLS TOOLBAR: TABS + SEARCH + SORTING -->
      <div class="p-4 border-b border-slate-800 space-y-3">
        
        <!-- Row 1: Lifecycle Tabs & Sorting -->
        <div class="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          
          <!-- Status Tabs -->
          <div class="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
            <button onclick="setFeedStatus('active')" id="tabActive" class="px-3 py-1.5 rounded-lg font-bold transition bg-blue-600 text-white shadow">
              <i class="fa-solid fa-bolt-lightning mr-1 text-[11px]"></i> Active Opportunities
            </button>
            <button onclick="setFeedStatus('closing_soon')" id="tabClosingSoon" class="px-3 py-1.5 rounded-lg font-bold transition text-slate-400 hover:text-white">
              <i class="fa-solid fa-hourglass-half mr-1 text-[11px] text-amber-400"></i> Closing Soon (&lt;24h)
            </button>
            <button onclick="setFeedStatus('expired')" id="tabExpired" class="px-3 py-1.5 rounded-lg font-bold transition text-slate-400 hover:text-white">
              <i class="fa-solid fa-archive mr-1 text-[11px]"></i> Expired Archive
            </button>
            <button onclick="setFeedStatus('all')" id="tabAll" class="px-3 py-1.5 rounded-lg font-bold transition text-slate-400 hover:text-white">
              All Records
            </button>
          </div>

          <!-- Sorting Dropdown -->
          <div class="flex items-center gap-2">
            <label for="sortBySelect" class="text-xs font-semibold text-slate-400 whitespace-nowrap">
              <i class="fa-solid fa-arrow-down-wide-short mr-1"></i> Sort:
            </label>
            <select id="sortBySelect" onchange="onSortChange()" class="px-3 py-1.5 rounded-xl bg-slate-950 text-slate-200 border border-slate-800 text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500">
              <option value="closing_soonest" selected>Closing Soonest (Default)</option>
              <option value="latest_published">Latest Published First</option>
              <option value="oldest_published">Oldest Published First</option>
              <option value="closing_latest">Closing Latest</option>
              <option value="newly_added">Newly Ingested First</option>
              <option value="highest_value">Highest Estimated Value</option>
              <option value="lowest_value">Lowest Estimated Value</option>
            </select>
          </div>

        </div>

        <!-- Row 2: Category Filters & Search Input -->
        <div class="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 pt-1">
          
          <!-- Category Quick Filters -->
          <div class="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            <button onclick="setCategoryFilter('')" data-cat="" class="cat-btn px-2.5 py-1 rounded-lg font-semibold bg-red-600 text-white flex-shrink-0">
              All Target Categories
            </button>
            <button onclick="setCategoryFilter('printer')" data-cat="printer" class="cat-btn px-2.5 py-1 rounded-lg font-semibold bg-slate-950 text-slate-300 hover:bg-slate-800 border border-slate-800 flex-shrink-0">
              Printers & MFP
            </button>
            <button onclick="setCategoryFilter('toner')" data-cat="toner" class="cat-btn px-2.5 py-1 rounded-lg font-semibold bg-slate-950 text-slate-300 hover:bg-slate-800 border border-slate-800 flex-shrink-0">
              Toner & Cartridges
            </button>
            <button onclick="setCategoryFilter('refill')" data-cat="refill" class="cat-btn px-2.5 py-1 rounded-lg font-semibold bg-slate-950 text-slate-300 hover:bg-slate-800 border border-slate-800 flex-shrink-0">
              Refill & Maintenance
            </button>
            <button onclick="setCategoryFilter('ink')" data-cat="ink" class="cat-btn px-2.5 py-1 rounded-lg font-semibold bg-slate-950 text-slate-300 hover:bg-slate-800 border border-slate-800 flex-shrink-0">
              OEM Ink & Drums
            </button>
          </div>

          <!-- Multi-Search Input -->
          <div class="relative w-full md:w-80">
            <i class="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs"></i>
            <input type="text" id="searchInput" oninput="onSearchInput()" placeholder="Filter Tender #, Dept, City, Item..." class="w-full pl-9 pr-8 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500">
            <button onclick="clearSearch()" id="btnClearSearch" class="hidden absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 text-xs">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

        </div>

      </div>

      <!-- TENDER DATA TABLE -->
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-950 text-slate-400 uppercase font-bold text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th class="py-3 px-4 w-44">Tender Number</th>
              <th class="py-3 px-4 w-64">Procuring Department</th>
              <th class="py-3 px-4 min-w-[200px]">Item & Category</th>
              <th class="py-3 px-4 w-40">Delivery Location</th>
              <th class="py-3 px-4 w-36">Published Date (IST)</th>
              <th class="py-3 px-4 w-44">Bid Deadline (IST)</th>
              <th class="py-3 px-4 w-28 text-center">Action</th>
            </tr>
          </thead>
          <tbody id="bidsTableBody" class="divide-y divide-slate-800/60 font-sans">
            <tr>
              <td colspan="7" class="py-14 text-center text-slate-400">
                <i class="fa-solid fa-circle-notch fa-spin text-2xl text-blue-500 mb-2 block"></i>
                <span>Loading verified GeM tenders...</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- TABLE FOOTER / PAGINATION SUMMARY -->
      <div class="p-3 bg-slate-950/60 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400 px-4">
        <div>
          Showing <span id="lblShownCount" class="font-bold text-white">0</span> of <span id="lblFilteredCount" class="font-bold text-white">0</span> tenders
        </div>
        <div class="flex items-center gap-2">
          <span>Source: <strong>Government e-Marketplace (GeM India)</strong></span>
        </div>
      </div>

    </div>

  </main>

  <!-- RED ALERT SIREN POPUP MODAL -->
  <div id="redAlertModal" class="hidden fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-slate-900 border-2 border-red-500 rounded-2xl max-w-lg w-full p-6 shadow-2xl shadow-red-500/20 text-center space-y-4">
      <div class="w-16 h-16 rounded-full bg-red-600/20 border-2 border-red-500 flex items-center justify-center text-red-500 mx-auto text-2xl radar-pulse">
        <i class="fa-solid fa-bell"></i>
      </div>
      <div>
        <span class="px-2.5 py-0.5 rounded text-[10px] font-black tracking-widest uppercase bg-red-600 text-white">MATCH ALERT DETECTED</span>
        <h2 id="modalTenderNo" class="text-xl font-black text-white font-mono mt-2 tracking-tight">--</h2>
        <p id="modalCategory" class="text-sm font-semibold text-slate-300 mt-1 line-clamp-2">--</p>
      </div>

      <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 text-left space-y-2 text-xs">
        <div>
          <span class="text-[10px] font-bold uppercase text-slate-500">Procuring Department</span>
          <p id="modalDept" class="font-bold text-slate-200 mt-0.5">--</p>
        </div>
        <div class="grid grid-cols-2 gap-2 pt-1">
          <div>
            <span class="text-[10px] font-bold uppercase text-slate-500">Verified Location</span>
            <p id="modalLocation" class="font-semibold text-slate-300 mt-0.5">--</p>
          </div>
          <div>
            <span class="text-[10px] font-bold uppercase text-slate-500">Bid Deadline (IST)</span>
            <p id="modalEndDate" class="font-mono font-bold text-amber-300 mt-0.5">--</p>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-center gap-3 pt-2">
        <button onclick="dismissSirenModal()" class="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 border border-slate-700 transition">
          Dismiss & Mute
        </button>
        <a id="modalDocLink" href="#" target="_blank" class="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-xs font-bold text-white shadow-lg shadow-red-600/30 transition flex items-center gap-1.5">
          <i class="fa-solid fa-file-pdf"></i>
          <span>View GeM Document</span>
        </a>
      </div>
    </div>
  </div>

  <!-- JAVASCRIPT APP LOGIC -->
  <script>
    // Global State
    let currentFeedStatus = 'active'; // 'active', 'closing_soon', 'expired', 'all'
    let currentSortBy = 'closing_soonest';
    let currentCategoryFilter = '';
    let searchQuery = '';
    let allBids = [];
    let activeAlertId = null;

    // Siren Audio Context
    let audioCtx = null;
    let sirenOsc = null;
    let sirenGain = null;
    let sirenTimer = null;
    let audioMuted = false;

    function getAudioContext() {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      return audioCtx;
    }

    function toggleAudioAlarm() {
      audioMuted = !audioMuted;
      const btn = document.getElementById('btnAlarmToggle');
      const icon = document.getElementById('alarmIcon');
      const text = document.getElementById('alarmText');

      if (audioMuted) {
        stopAudioSiren();
        btn.className = "px-3 py-1.5 rounded-lg text-xs font-bold border transition flex items-center gap-2 bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700";
        icon.className = "fa-solid fa-volume-xmark";
        text.textContent = "Siren: MUTED";
      } else {
        btn.className = "px-3 py-1.5 rounded-lg text-xs font-bold border transition flex items-center gap-2 bg-red-950/40 text-red-400 border-red-500/30 hover:bg-red-900/50";
        icon.className = "fa-solid fa-volume-high";
        text.textContent = "Siren: ON";
      }
    }

    function playAudioSiren() {
      if (audioMuted) return;
      try {
        const ctx = getAudioContext();
        if (ctx.state === 'suspended') ctx.resume();
        if (sirenOsc) return;

        sirenOsc = ctx.createOscillator();
        sirenGain = ctx.createGain();
        sirenOsc.type = 'sawtooth';
        sirenOsc.frequency.setValueAtTime(800, ctx.currentTime);

        let high = false;
        sirenTimer = setInterval(() => {
          if (!sirenOsc) return;
          sirenOsc.frequency.setValueAtTime(high ? 800 : 1200, ctx.currentTime);
          high = !high;
        }, 350);

        sirenGain.gain.setValueAtTime(0.25, ctx.currentTime);
        sirenOsc.connect(sirenGain);
        sirenGain.connect(ctx.destination);
        sirenOsc.start();
      } catch (e) {
        console.warn('Audio notice:', e);
      }
    }

    function stopAudioSiren() {
      if (sirenTimer) { clearInterval(sirenTimer); sirenTimer = null; }
      if (sirenOsc) {
        try { sirenOsc.stop(); sirenOsc.disconnect(); } catch (e) {}
        sirenOsc = null;
      }
    }

    function dismissSirenModal() {
      stopAudioSiren();
      document.getElementById('redAlertModal').classList.add('hidden');
    }

    // --- DATA LOADING ---
    async function loadDashboardData() {
      try {
        // Fetch Bids with server-side status & sorting
        const url = `/bids/?status=${encodeURIComponent(currentFeedStatus)}&sort_by=${encodeURIComponent(currentSortBy)}&limit=200`;
        const [bidsRes, statsRes, alertsRes, healthRes] = await Promise.allSettled([
          fetch(url).then(r => r.ok ? r.json() : []),
          fetch('/bids/summary/stats').then(r => r.ok ? r.json() : null),
          fetch('/alerts/stats').then(r => r.ok ? r.json() : null),
          fetch('/health/').then(r => r.ok ? r.json() : null),
        ]);

        if (bidsRes.status === 'fulfilled') {
          allBids = bidsRes.value || [];
          renderBidsTable();
        }

        // Exact DB summary counts
        if (statsRes.status === 'fulfilled' && statsRes.value) {
          const s = statsRes.value;
          document.getElementById('statActiveBids').textContent = `${s.active_bids} Active`;
          document.getElementById('statTotalBids').textContent = `${s.total_bids} Total Tracked`;
          document.getElementById('statExpiredBids').textContent = `${s.expired_bids} Expired`;
        }

        // Exact Alert Stats
        if (alertsRes.status === 'fulfilled' && alertsRes.value) {
          const a = alertsRes.value;
          document.getElementById('statAlerts').textContent = `${a.total_alerts} Alerts`;
          document.getElementById('statUnackAlerts').textContent = `${a.unacknowledged_alerts} Pending Action`;
        }

        // Engine Status
        if (healthRes.status === 'fulfilled' && healthRes.value) {
          const h = healthRes.value;
          document.getElementById('statHealth').innerHTML = h.monitor_running
            ? `<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span><span>24/7 Monitoring</span>`
            : `<span class="w-2 h-2 rounded-full bg-amber-500"></span><span>Engine Paused</span>`;
        }

        // Check if there is an unacknowledged alert to trigger banner/siren
        checkUnacknowledgedAlerts();

      } catch (err) {
        console.error('Dashboard load error:', err);
      }
    }

    async function checkUnacknowledgedAlerts() {
      try {
        const res = await fetch('/alerts/?limit=1&unacknowledged_only=true');
        if (!res.ok) return;
        const alerts = await res.json();
        if (alerts && alerts.length > 0) {
          const topAlert = alerts[0];
          activeAlertId = topAlert.id;
          const bid = topAlert.bid;
          if (bid) {
            renderActiveBanner(topAlert, bid);
            // Trigger siren only for unacknowledged alerts
            playAudioSiren();
          }
        }
      } catch (e) {
        console.warn('Alerts check error:', e);
      }
    }

    function renderActiveBanner(alert, bid) {
      document.getElementById('bannerTenderNo').textContent = bid.bid_number || 'Tender Alert';
      document.getElementById('bannerLocation').textContent = bid.display_location || 'Location Not Available';
      document.getElementById('bannerDept').textContent = bid.dept_name || bid.ministry_name || 'Government Organization';
      document.getElementById('bannerCat').textContent = bid.category_name || '';
      document.getElementById('bannerDeadline').textContent = `${bid.end_date_formatted || 'N/A'} (${bid.time_remaining || ''})`;
      document.getElementById('bannerDocLink').href = bid.bid_url || '#';
      document.getElementById('activeAlertBanner').classList.remove('hidden');
    }

    async function ackCurrentBannerAlert() {
      if (!activeAlertId) return;
      try {
        await fetch(`/alerts/${activeAlertId}/ack`, { method: 'POST' });
        stopAudioSiren();
        document.getElementById('activeAlertBanner').classList.add('hidden');
        loadDashboardData();
      } catch (e) {
        console.error('Ack error:', e);
      }
    }

    // --- TABLE FILTERING & RENDERING ---
    function matchesCategory(catName, filterKey) {
      if (!filterKey) return true;
      if (!catName) return false;
      const t = catName.toLowerCase();
      if (filterKey === 'printer') return /\\b(printers?|mfp)\\b/i.test(t);
      if (filterKey === 'toner') return /\\b(toner|cartridge|c(?:a|ar)tridge)\\b/i.test(t);
      if (filterKey === 'refill') return /\\b(refill|roller|maintenance|repair)\\b/i.test(t);
      if (filterKey === 'ink') return /\\b(ink(?:jet|s)?|drum|ribbon)\\b/i.test(t);
      return true;
    }

    function renderBidsTable() {
      const tbody = document.getElementById('bidsTableBody');
      const q = searchQuery.toLowerCase().trim();

      let filtered = allBids;

      if (currentCategoryFilter) {
        filtered = filtered.filter(b => matchesCategory(b.category_name, currentCategoryFilter));
      }

      if (q) {
        filtered = filtered.filter(b =>
          (b.bid_number && b.bid_number.toLowerCase().includes(q)) ||
          (b.category_name && b.category_name.toLowerCase().includes(q)) ||
          (b.dept_name && b.dept_name.toLowerCase().includes(q)) ||
          (b.display_location && b.display_location.toLowerCase().includes(q)) ||
          (b.consignee_city && b.consignee_city.toLowerCase().includes(q)) ||
          (b.consignee_state && b.consignee_state.toLowerCase().includes(q))
        );
      }

      document.getElementById('lblShownCount').textContent = filtered.length;
      document.getElementById('lblFilteredCount').textContent = allBids.length;

      if (!filtered || filtered.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" class="py-14 text-center text-slate-400">
              <i class="fa-solid fa-filter-circle-xmark text-3xl mb-2 text-slate-600 block"></i>
              <p class="font-bold text-slate-300">No tenders match selected criteria</p>
              <p class="text-xs text-slate-500 mt-1">Try switching tabs or resetting search filters.</p>
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = filtered.map(b => {
        const bidNo = escapeHtml(b.bid_number);
        const dept = escapeHtml(b.dept_name || b.ministry_name || 'Not available from source');
        const min = b.ministry_name && b.ministry_name !== b.dept_name ? escapeHtml(b.ministry_name) : '';
        const cat = escapeHtml(b.category_name || 'Unspecified Category');
        const loc = escapeHtml(b.display_location || 'Not available from source');
        const pubDate = escapeHtml(b.published_date || 'Not available');
        const pubTime = b.published_time ? escapeHtml(b.published_time) : '';
        const endDate = escapeHtml(b.end_date_formatted || 'Not available');
        const endTime = b.end_time_formatted ? escapeHtml(b.end_time_formatted) : '';
        const timeRem = escapeHtml(b.time_remaining || '');
        const isExp = b.bid_status === 'EXPIRED';

        // Provenance & Status Pills
        const provBadge = b.data_source_classification === 'LIVE_VERIFIED'
          ? '<span class="px-1.5 py-0.2 rounded text-[9px] font-black bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">LIVE</span>'
          : '<span class="px-1.5 py-0.2 rounded text-[9px] font-black bg-blue-500/10 text-blue-400 border border-blue-500/20">IMPORTED</span>';

        const statusBadge = isExp
          ? '<span class="px-1.5 py-0.2 rounded text-[9px] font-black bg-slate-800 text-slate-400 border border-slate-700">EXPIRED</span>'
          : '<span class="px-1.5 py-0.2 rounded text-[9px] font-black bg-red-600/20 text-red-400 border border-red-500/30">MATCH</span>';

        const locBadge = b.location_verification_status === 'VERIFIED'
          ? '<span class="text-[9px] text-emerald-400" title="Verified Administrative Location"><i class="fa-solid fa-circle-check"></i></span>'
          : '';

        const rowBg = isExp ? 'bg-slate-950/20 opacity-60 hover:opacity-100 hover:bg-slate-900/40' : 'bg-slate-950/40 hover:bg-slate-900/70';

        return `
          <tr class="transition ${rowBg}">
            <!-- Tender Number & Provenance -->
            <td class="py-3 px-4 font-mono font-bold text-white whitespace-nowrap align-top">
              <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full ${isExp ? 'bg-slate-600' : 'bg-red-500'}"></span>
                <span class="select-all tracking-tight">${bidNo}</span>
                <button onclick="copyToClipboard('${bidNo}')" class="text-slate-500 hover:text-slate-300 p-1" title="Copy Tender No">
                  <i class="fa-regular fa-copy text-[10px]"></i>
                </button>
              </div>
              <div class="flex items-center gap-1 mt-1">
                ${statusBadge}
                ${provBadge}
              </div>
            </td>

            <!-- Procuring Department -->
            <td class="py-3 px-4 align-top">
              <div class="font-bold text-slate-100 flex items-start gap-1.5">
                <i class="fa-solid fa-building text-[11px] text-sky-400 flex-shrink-0 mt-0.5"></i>
                <span class="line-clamp-2">${dept}</span>
              </div>
              ${min ? `<div class="text-[11px] text-slate-400 mt-0.5 line-clamp-1">${min}</div>` : ''}
            </td>

            <!-- Category & Specification -->
            <td class="py-3 px-4 align-top">
              <div class="font-semibold text-slate-200 line-clamp-2">${cat}</div>
            </td>

            <!-- Delivery Location -->
            <td class="py-3 px-4 whitespace-nowrap align-top">
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-300 border border-slate-800 text-[11px]">
                <i class="fa-solid fa-location-dot ${isExp ? 'text-slate-500' : 'text-red-400'}"></i>
                <span>${loc}</span>
                ${locBadge}
              </span>
            </td>

            <!-- Published Date (IST) -->
            <td class="py-3 px-4 whitespace-nowrap align-top text-slate-300">
              <div class="font-mono text-[11px] font-semibold">${pubDate}</div>
              ${pubTime ? `<div class="text-[10px] text-slate-500 font-mono">${pubTime}</div>` : ''}
            </td>

            <!-- Bid Deadline (IST) & Time Remaining -->
            <td class="py-3 px-4 whitespace-nowrap align-top">
              <div class="font-mono text-[11px] font-bold ${isExp ? 'text-slate-500' : 'text-amber-300'}">${endDate}</div>
              ${endTime ? `<div class="text-[10px] text-slate-400 font-mono">${endTime}</div>` : ''}
              ${timeRem ? `<div class="text-[10px] font-semibold ${isExp ? 'text-slate-500' : 'text-emerald-400'} mt-0.5">${timeRem}</div>` : ''}
            </td>

            <!-- Action Link -->
            <td class="py-3 px-4 whitespace-nowrap align-top text-center">
              ${b.bid_url ? `
                <a href="${b.bid_url}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-red-600 text-slate-300 hover:text-white border border-slate-700 hover:border-red-500 transition text-[11px] font-bold">
                  <i class="fa-solid fa-file-pdf"></i>
                  <span>PDF</span>
                </a>
              ` : '<span class="text-slate-600">N/A</span>'}
            </td>
          </tr>
        `;
      }).join('');
    }

    // --- INTERACTION HANDLERS ---
    function setFeedStatus(status) {
      currentFeedStatus = status;
      ['tabActive', 'tabClosingSoon', 'tabExpired', 'tabAll'].forEach(id => {
        const btn = document.getElementById(id);
        if ((status === 'active' && id === 'tabActive') ||
            (status === 'closing_soon' && id === 'tabClosingSoon') ||
            (status === 'expired' && id === 'tabExpired') ||
            (status === 'all' && id === 'tabAll')) {
          btn.className = "px-3 py-1.5 rounded-lg font-bold transition bg-blue-600 text-white shadow";
        } else {
          btn.className = "px-3 py-1.5 rounded-lg font-bold transition text-slate-400 hover:text-white";
        }
      });
      loadDashboardData();
    }

    function onSortChange() {
      currentSortBy = document.getElementById('sortBySelect').value;
      loadDashboardData();
    }

    function setCategoryFilter(catKey) {
      currentCategoryFilter = catKey.toLowerCase();
      document.querySelectorAll('.cat-btn').forEach(btn => {
        if (btn.getAttribute('data-cat') === catKey) {
          btn.className = "cat-btn px-2.5 py-1 rounded-lg font-semibold bg-red-600 text-white flex-shrink-0";
        } else {
          btn.className = "cat-btn px-2.5 py-1 rounded-lg font-semibold bg-slate-950 text-slate-300 hover:bg-slate-800 border border-slate-800 flex-shrink-0";
        }
      });
      renderBidsTable();
    }

    function onSearchInput() {
      searchQuery = document.getElementById('searchInput').value;
      const btnClear = document.getElementById('btnClearSearch');
      if (searchQuery) {
        btnClear.classList.remove('hidden');
      } else {
        btnClear.classList.add('hidden');
      }
      renderBidsTable();
    }

    function clearSearch() {
      document.getElementById('searchInput').value = '';
      document.getElementById('btnClearSearch').classList.add('hidden');
      searchQuery = '';
      renderBidsTable();
    }

    function copyToClipboard(text) {
      navigator.clipboard.writeText(text).then(() => {
        const toast = document.createElement('div');
        toast.className = 'fixed bottom-4 right-4 z-50 bg-slate-900 border border-blue-500 text-white px-4 py-2 rounded-xl shadow-xl text-xs font-mono font-bold flex items-center gap-2';
        toast.innerHTML = '<i class="fa-solid fa-check text-emerald-400"></i> Tender # Copied: ' + text;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2200);
      });
    }

    function triggerImmediateRefresh() {
      const icon = document.getElementById('refreshIcon');
      icon.classList.add('fa-spin');
      fetch('/health/trigger-poll', { method: 'POST' }).finally(() => {
        setTimeout(loadDashboardData, 1200);
        setTimeout(() => icon.classList.remove('fa-spin'), 1500);
      });
    }

    function escapeHtml(text) {
      if (!text) return '';
      const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
      return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    // --- AUTO-REFRESH TIMER LOOP (15 Seconds) ---
    let refreshSeconds = 15;
    setInterval(() => {
      refreshSeconds--;
      const el = document.getElementById('refreshTimer');
      if (el) el.textContent = `${refreshSeconds}s`;
      if (refreshSeconds <= 0) {
        refreshSeconds = 15;
        loadDashboardData();
      }
    }, 1000);

    // Initial Load
    document.addEventListener('DOMContentLoaded', loadDashboardData);
  </script>

</body>
</html>
"""

@router.get("/dashboard", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def get_dashboard():
    return DASHBOARD_HTML
