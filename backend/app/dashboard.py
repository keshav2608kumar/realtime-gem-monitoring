"""
GeM BidWatch — Executive Live Web Dashboard
Clean, clutter-free, professional real-time monitoring interface for GeM Tenders.
Target: Bangalore / Karnataka — Printers, Toner Cartridges, Refilling & Consumables.
"""

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GeM BidWatch — 24/7 Bangalore Tenders Live Monitor</title>
  
  <!-- Fonts & Icons -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
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
            slate: {
              850: '#111827',
              900: '#0B1120',
              925: '#070C18',
              950: '#030712',
            }
          }
        }
      }
    }
  </script>

  <style>
    body {
      background: radial-gradient(circle at 50% 0%, #0d1a33 0%, #060a14 50%, #03060c 100%);
      min-height: 100vh;
      color: #f1f5f9;
      font-feature-settings: "cv02", "cv03", "cv04", "cv11";
    }
    .glass-panel {
      background: rgba(11, 17, 32, 0.75);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }
    .custom-scrollbar::-webkit-scrollbar {
      height: 6px;
      width: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
      background: #0b1120;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: #1e293b;
      border-radius: 9999px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
      background: #334155;
    }
    @keyframes siren-glow {
      0%, 100% { box-shadow: 0 0 15px rgba(239, 68, 68, 0.4), inset 0 0 15px rgba(239, 68, 68, 0.2); }
      50% { box-shadow: 0 0 30px rgba(239, 68, 68, 0.8), inset 0 0 25px rgba(239, 68, 68, 0.4); }
    }
    .siren-active {
      animation: siren-glow 2s infinite ease-in-out;
    }
  </style>
</head>
<body class="font-sans antialiased selection:bg-red-500 selection:text-white">

  <!-- TOP EXECUTIVE NAVBAR -->
  <header class="border-b border-slate-800/80 glass-panel sticky top-0 z-40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
      
      <!-- Logo & Live Indicator -->
      <div class="flex items-center space-x-3 min-w-0">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-red-600 to-rose-500 flex items-center justify-center text-white shadow-lg shadow-red-600/30 flex-shrink-0">
          <i class="fa-solid fa-radar text-lg animate-pulse"></i>
        </div>
        <div class="min-w-0">
          <div class="flex items-center space-x-2">
            <span class="text-base sm:text-lg font-black tracking-tight text-white font-mono">GeM BidWatch</span>
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-ping"></span>
              24/7 LIVE
            </span>
          </div>
          <p class="text-[11px] text-slate-400 truncate">Bangalore &amp; Karnataka &bull; Printers, Cartridges &amp; Consumables</p>
        </div>
      </div>

      <!-- Controls: Alarm Mute/Unmute, Auto-Sync, Download APK -->
      <div class="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
        
        <!-- Alarm Sound Toggle Button -->
        <button id="btnAlarmToggle" onclick="toggleAlarmSound()" class="px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20" title="Click to Toggle Siren Sound">
          <i id="alarmIcon" class="fa-solid fa-volume-high"></i>
          <span id="alarmStatusText" class="hidden sm:inline">Siren Sound: ON</span>
        </button>

        <!-- Auto-Refresh Indicator -->
        <div class="hidden md:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-[11px] text-slate-400">
          <i class="fa-solid fa-rotate-right fa-spin text-slate-500 text-[10px]"></i>
          <span>Syncing in <strong id="refreshTimer" class="text-slate-200 font-mono">15s</strong></span>
        </div>

        <!-- Manual Poll Button -->
        <button onclick="triggerManualScan()" class="p-2 sm:px-3 sm:py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition flex items-center gap-1.5" title="Scan GeM Immediately">
          <i id="scanIcon" class="fa-solid fa-arrows-rotate"></i>
          <span class="hidden sm:inline">Scan Now</span>
        </button>

        <!-- Download APK Button -->
        <a href="https://github.com/keshav2608kumar/realtime-gem-monitoring/releases/download/v1.0.0/GeM_BidWatch.apk" class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-950/50 flex items-center gap-1.5 transition">
          <i class="fa-brands fa-android text-sm"></i>
          <span class="hidden sm:inline">Download APK</span>
        </a>
      </div>

    </div>
  </header>

  <!-- MAIN CONTAINER -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">

    <!-- EXECUTIVE METRICS ROW -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      
      <!-- Metric 1: Cloud Engine Status -->
      <div class="glass-panel rounded-2xl p-4 border border-slate-800 flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 text-lg flex-shrink-0">
          <i class="fa-solid fa-server"></i>
        </div>
        <div class="min-w-0">
          <p class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Engine Status</p>
          <p id="statHealth" class="text-sm sm:text-base font-black text-emerald-400 truncate">24/7 Monitoring</p>
          <p class="text-[10px] text-slate-500 truncate">Auto-Sync Active</p>
        </div>
      </div>

      <!-- Metric 2: Region -->
      <div class="glass-panel rounded-2xl p-4 border border-slate-800 flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 text-lg flex-shrink-0">
          <i class="fa-solid fa-location-dot"></i>
        </div>
        <div class="min-w-0">
          <p class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Target Region</p>
          <p class="text-sm sm:text-base font-black text-white truncate">Bangalore Urban</p>
          <p class="text-[10px] text-slate-500 truncate">KARNATAKA, India</p>
        </div>
      </div>

      <!-- Metric 3: Target Category -->
      <div class="glass-panel rounded-2xl p-4 border border-slate-800 flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 text-lg flex-shrink-0">
          <i class="fa-solid fa-print"></i>
        </div>
        <div class="min-w-0">
          <p class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Target Scope</p>
          <p class="text-sm sm:text-base font-black text-amber-300 truncate">Printers &amp; Toners</p>
          <p class="text-[10px] text-slate-500 truncate">Cartridges &amp; Refilling</p>
        </div>
      </div>

      <!-- Metric 4: Live Target Bids -->
      <div class="glass-panel rounded-2xl p-4 border border-slate-800 flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 text-lg flex-shrink-0">
          <i class="fa-solid fa-bell"></i>
        </div>
        <div class="min-w-0">
          <p class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Target Tenders</p>
          <p id="statBidsCount" class="text-sm sm:text-base font-black text-rose-400 truncate">15 Verified</p>
          <p id="statAlerts" class="text-[10px] text-slate-500 truncate">15 Alerts Live</p>
        </div>
      </div>

    </div>

    <!-- URGENT ACTIVE ALERT BANNER (High Visibility) -->
    <div id="activeAlertBanner" class="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-red-950 via-slate-900 to-red-950 border-2 border-red-500 shadow-xl siren-active flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="flex items-start sm:items-center gap-3.5 min-w-0">
        <div class="w-11 h-11 rounded-xl bg-red-600 text-white flex items-center justify-center text-lg flex-shrink-0 shadow-lg shadow-red-600/50 animate-pulse">
          <i class="fa-solid fa-triangle-exclamation"></i>
        </div>
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <span class="px-2 py-0.5 rounded text-[10px] font-black bg-red-600 text-white tracking-wider uppercase">
              🚨 TARGET MATCH DETECTED
            </span>
            <span id="bannerBidNo" class="font-mono font-bold text-white text-sm select-all">GEM/2026/B/8123875</span>
            <span id="bannerLocation" class="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">Bangalore Urban</span>
          </div>
          
          <!-- Department & Category -->
          <div class="mt-1">
            <p id="bannerDept" class="text-xs font-bold text-sky-300 flex items-center gap-1.5">
              <i class="fa-solid fa-building-columns text-[10px] text-sky-400"></i>
              <span>ISRO Satellite Centre (URSC), Bangalore</span>
            </p>
            <p id="bannerCategory" class="text-sm font-extrabold text-white mt-0.5">Computer Printer (V2) - Monochrome duplex laser printers</p>
          </div>
        </div>
      </div>

      <!-- Deadline & Action Button -->
      <div class="flex items-center gap-3 flex-shrink-0 self-end md:self-center">
        <div class="text-right">
          <p class="text-[10px] uppercase font-bold text-slate-400">Bid Deadline</p>
          <p id="bannerDeadline" class="text-xs sm:text-sm font-black text-amber-300 font-mono flex items-center gap-1">
            <i class="fa-solid fa-clock text-amber-400 text-[11px]"></i>
            <span>16 Nov 2026, 03:00 PM</span>
          </p>
        </div>
        <a id="bannerDocLink" href="https://bidplus.gem.gov.in/showbidDocument/8123875" target="_blank" class="px-4 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-950/60 flex items-center gap-1.5 transition">
          <i class="fa-solid fa-file-pdf"></i>
          <span>View GeM PDF</span>
        </a>
      </div>
    </div>

    <!-- FILTER TOOLBAR -->
    <div class="glass-panel rounded-2xl p-4 border border-slate-800 space-y-3">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
        
        <!-- Search Input -->
        <div class="relative w-full sm:w-96">
          <i class="fa-solid fa-magnifying-glass absolute left-3.5 top-3 text-slate-500 text-xs"></i>
          <input type="text" id="searchInput" oninput="filterBids()" placeholder="Filter by Tender #, Department, Category..." class="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition shadow-inner">
        </div>

        <!-- Category Filter Chips with Live Badges -->
        <div class="flex items-center space-x-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0 custom-scrollbar">
          <button onclick="setCategoryFilter('')" class="cat-filter-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-red-600 text-white shadow-md shadow-red-600/30 flex items-center gap-1.5 flex-shrink-0" data-cat="">
            <span>All Target Tenders</span>
            <span id="countAll" class="px-1.5 py-0.2 rounded-full text-[10px] bg-black/40 text-slate-200">15</span>
          </button>
          <button onclick="setCategoryFilter('printer')" class="cat-filter-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800 flex items-center gap-1.5 flex-shrink-0" data-cat="printer">
            <span>Printers</span>
            <span id="countPrinter" class="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-amber-300">0</span>
          </button>
          <button onclick="setCategoryFilter('toner')" class="cat-filter-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800 flex items-center gap-1.5 flex-shrink-0" data-cat="toner">
            <span>Toner Cartridges</span>
            <span id="countToner" class="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-amber-300">0</span>
          </button>
          <button onclick="setCategoryFilter('refill')" class="cat-filter-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800 flex items-center gap-1.5 flex-shrink-0" data-cat="refill">
            <span>Refilling &amp; Maint.</span>
            <span id="countRefill" class="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-amber-300">0</span>
          </button>
          <button onclick="setCategoryFilter('ink')" class="cat-filter-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800 flex items-center gap-1.5 flex-shrink-0" data-cat="ink">
            <span>Ink &amp; Drum</span>
            <span id="countInk" class="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-amber-300">0</span>
          </button>
        </div>

      </div>
    </div>

    <!-- MAIN TENDERS TABLE (CLEAN, PROPERLY ALIGNED) -->
    <div class="glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
      <div class="overflow-x-auto custom-scrollbar">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-900/90 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-bold">
            <tr>
              <th class="py-3.5 px-4 w-48">Tender / Bid #</th>
              <th class="py-3.5 px-4 min-w-[220px]">Procuring Department</th>
              <th class="py-3.5 px-4 min-w-[260px]">Item Description &amp; Category</th>
              <th class="py-3.5 px-4 w-36">Location</th>
              <th class="py-3.5 px-4 w-44">Bid Deadline</th>
              <th class="py-3.5 px-4 text-right w-28">Action</th>
            </tr>
          </thead>
          <tbody id="bidsTableBody" class="divide-y divide-slate-800/60 font-medium">
            <tr>
              <td colspan="6" class="py-16 text-center text-slate-500">
                <i class="fa-solid fa-spinner fa-spin text-2xl text-red-500 mb-3 block"></i>
                <p class="font-semibold text-slate-300">Loading verified Bangalore tenders...</p>
                <p class="text-[11px] text-slate-500 mt-1">Connecting to GeM BidWatch engine</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </main>

  <!-- CLEAN FOOTER -->
  <footer class="border-t border-slate-800/80 bg-slate-925 py-4 text-xs text-slate-500 mt-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
      <p>GeM BidWatch &bull; Real-time 24/7 Bidding Alert Engine for Government e-Marketplace (GeM India)</p>
      <p class="font-mono text-slate-600">Bangalore Target Edition v2.0</p>
    </div>
  </footer>

  <!-- FULL SCREEN RED SIREN POPUP (Only when target bid triggers) -->
  <div id="redAlertModal" class="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 hidden">
    <div class="max-w-md w-full bg-gradient-to-b from-red-950 via-slate-900 to-slate-950 border-2 border-red-500 rounded-3xl p-6 shadow-2xl text-center relative overflow-hidden siren-active">
      <div class="w-16 h-16 rounded-full bg-red-600 text-white flex items-center justify-center mx-auto text-2xl shadow-xl shadow-red-600/60 animate-bounce mb-3">
        <i class="fa-solid fa-bell"></i>
      </div>
      <h2 class="text-xl font-black text-white uppercase tracking-tight">🚨 TARGET BID MATCH DETECTED!</h2>
      <p id="modalLocation" class="text-xs text-slate-300 font-semibold mt-1">Bangalore Urban, KARNATAKA</p>
      
      <div class="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-left my-4 space-y-2">
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400">Department</span>
          <p id="modalDept" class="text-xs font-bold text-sky-300">ISRO Satellite Centre (URSC), Bangalore</p>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400">Bid Number</span>
          <p id="modalBidNo" class="text-sm font-black text-white font-mono select-all">GEM/2026/B/8123875</p>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400">Category</span>
          <p id="modalCategory" class="text-xs font-semibold text-slate-200">Computer Printer (V2)</p>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400">Bid End Date / Deadline</span>
          <p id="modalEndDate" class="text-xs font-black text-amber-300 font-mono">16 Nov 2026, 03:00 PM</p>
        </div>
      </div>

      <div class="space-y-2">
        <a id="modalDocLink" href="#" target="_blank" class="w-full py-3 rounded-xl text-sm font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white flex items-center justify-center gap-2 shadow-lg transition">
          <i class="fa-solid fa-file-pdf"></i>
          <span>Open GeM Official Document</span>
        </a>
        <button onclick="dismissSirenModal()" class="w-full py-2.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-300 transition">
          Silence Siren &amp; Dismiss
        </button>
      </div>
    </div>
  </div>

  <!-- JAVASCRIPT LOGIC -->
  <script>
    let allBids = [];
    let activeCategoryFilter = '';
    let isAudioAlarmEnabled = true;
    let audioCtx = null;
    let sirenOsc = null;
    let sirenGain = null;
    let sirenTimer = null;
    let countdownSecs = 15;

    // --- AUDIO SIREN SYNTHESIZER ---
    function toggleAlarmSound() {
      isAudioAlarmEnabled = !isAudioAlarmEnabled;
      const btn = document.getElementById('btnAlarmToggle');
      const icon = document.getElementById('alarmIcon');
      const txt = document.getElementById('alarmStatusText');
      if (isAudioAlarmEnabled) {
        btn.className = "px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20";
        icon.className = "fa-solid fa-volume-high";
        txt.textContent = "Siren Sound: ON";
      } else {
        stopAudioSiren();
        btn.className = "px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700";
        icon.className = "fa-solid fa-volume-xmark";
        txt.textContent = "Siren Sound: MUTED";
      }
    }

    function playAudioSiren() {
      if (!isAudioAlarmEnabled) return;
      try {
        if (!audioCtx) {
          audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
          audioCtx.resume();
        }
        if (sirenOsc) return; // already playing

        sirenOsc = audioCtx.createOscillator();
        sirenGain = audioCtx.createGain();
        sirenOsc.type = 'sawtooth';
        sirenOsc.frequency.setValueAtTime(800, audioCtx.currentTime);

        let high = false;
        sirenTimer = setInterval(() => {
          if (!sirenOsc) return;
          sirenOsc.frequency.setValueAtTime(high ? 800 : 1200, audioCtx.currentTime);
          high = !high;
        }, 350);

        sirenGain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        sirenOsc.connect(sirenGain);
        sirenGain.connect(audioCtx.destination);
        sirenOsc.start();
      } catch (e) {
        console.warn('AudioContext notice:', e);
      }
    }

    function stopAudioSiren() {
      if (sirenTimer) {
        clearInterval(sirenTimer);
        sirenTimer = null;
      }
      if (sirenOsc) {
        try {
          sirenOsc.stop();
          sirenOsc.disconnect();
        } catch (e) {}
        sirenOsc = null;
      }
    }

    function dismissSirenModal() {
      stopAudioSiren();
      document.getElementById('redAlertModal').classList.add('hidden');
    }

    // --- DATA FETCHING & SYNCHRONIZATION ---
    async function loadDashboardData() {
      try {
        const [hRes, aRes, bRes] = await Promise.allSettled([
          fetch('/health/').then(r => r.ok ? r.json() : null),
          fetch('/alerts/?limit=20').then(r => r.ok ? r.json() : null),
          fetch('/bids/?limit=100').then(r => r.ok ? r.json() : null)
        ]);

        if (hRes.status === 'fulfilled' && hRes.value) {
          const h = hRes.value;
          document.getElementById('statHealth').textContent = h.monitor_running ? '24/7 Monitoring' : 'Paused';
        }

        if (aRes.status === 'fulfilled' && aRes.value) {
          const alerts = aRes.value;
          document.getElementById('statAlerts').textContent = `${alerts.length} Alerts Live`;
          if (alerts.length > 0) {
            renderActiveBanner(alerts[0]);
          }
        }

        if (bRes.status === 'fulfilled' && bRes.value) {
          allBids = bRes.value;
          document.getElementById('statBidsCount').textContent = `${allBids.length} Verified`;
          updateCategoryCountBadges();
          filterBids();
        }
      } catch (err) {
        console.error('Data load error:', err);
      }
    }

    function renderActiveBanner(alert) {
      if (!alert || !alert.bid) return;
      const b = alert.bid;
      const banner = document.getElementById('activeAlertBanner');
      if (!banner) return;

      document.getElementById('bannerBidNo').textContent = b.bid_number;
      document.getElementById('bannerDept').innerHTML = `<i class="fa-solid fa-building-columns text-[10px] text-sky-400"></i> <span>${escapeHtml(b.dept_name || b.ministry_name || 'Government of Karnataka')}</span>`;
      document.getElementById('bannerCategory').textContent = b.category_name;
      document.getElementById('bannerLocation').textContent = `${b.consignee_city || 'Bangalore Urban'}, ${b.consignee_state || 'KARNATAKA'}`;

      const deadline = b.end_date
        ? new Date(b.end_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
        : '16 Nov 2026, 03:00 PM';
      document.getElementById('bannerDeadline').innerHTML = `<i class="fa-solid fa-clock text-amber-400 text-[11px]"></i> <span>${deadline}</span>`;

      if (b.bid_url) {
        document.getElementById('bannerDocLink').href = b.bid_url;
      }
      banner.classList.remove('hidden');
    }

    // --- CATEGORY MATCHING & COUNTS ---
    function matchesCat(category, filterKey) {
      if (!category) return false;
      const text = category.toLowerCase();
      if (filterKey === 'printer') return /\bprinter|mfp/i.test(text);
      if (filterKey === 'toner') return /\btoner|cartridge|cart/i.test(text);
      if (filterKey === 'refill') return /refill|roller|maintenance|repair/i.test(text);
      if (filterKey === 'ink') return /\bink|drum|ribbon/i.test(text);
      return true;
    }

    function updateCategoryCountBadges() {
      const elAll = document.getElementById('countAll');
      const elPrin = document.getElementById('countPrinter');
      const elTon = document.getElementById('countToner');
      const elRef = document.getElementById('countRefill');
      const elInk = document.getElementById('countInk');

      if (elAll) elAll.textContent = allBids.length;
      if (elPrin) elPrin.textContent = allBids.filter(b => matchesCat(b.category_name, 'printer')).length;
      if (elTon) elTon.textContent = allBids.filter(b => matchesCat(b.category_name, 'toner')).length;
      if (elRef) elRef.textContent = allBids.filter(b => matchesCat(b.category_name, 'refill')).length;
      if (elInk) elInk.textContent = allBids.filter(b => matchesCat(b.category_name, 'ink')).length;
    }

    function setCategoryFilter(catKey) {
      activeCategoryFilter = catKey.toLowerCase();
      document.querySelectorAll('.cat-filter-btn').forEach(btn => {
        if (btn.getAttribute('data-cat') === catKey) {
          btn.className = "cat-filter-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-red-600 text-white shadow-md shadow-red-600/30 flex items-center gap-1.5 flex-shrink-0";
        } else {
          btn.className = "cat-filter-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800 flex items-center gap-1.5 flex-shrink-0";
        }
      });
      filterBids();
    }

    function filterBids() {
      const q = (document.getElementById('searchInput').value || '').toLowerCase().trim();
      let filtered = allBids;
      if (activeCategoryFilter) {
        filtered = filtered.filter(b => matchesCat(b.category_name, activeCategoryFilter));
      }
      if (q) {
        filtered = filtered.filter(b =>
          (b.bid_number && b.bid_number.toLowerCase().includes(q)) ||
          (b.category_name && b.category_name.toLowerCase().includes(q)) ||
          (b.dept_name && b.dept_name.toLowerCase().includes(q)) ||
          (b.consignee_city && b.consignee_city.toLowerCase().includes(q))
        );
      }
      renderBids(filtered);
    }

    function renderBids(bids) {
      const tbody = document.getElementById('bidsTableBody');
      if (!bids || bids.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" class="py-14 text-center text-slate-400">
              <i class="fa-solid fa-filter-circle-xmark text-3xl mb-2 text-slate-600 block"></i>
              <p class="font-bold text-slate-300">No tenders match selected filter</p>
              <p class="text-xs text-slate-500 mt-1">Click "All Target Tenders" to view all active Bangalore listings.</p>
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = bids.map(b => {
        const cat = escapeHtml(b.category_name);
        const dept = escapeHtml(b.dept_name || b.ministry_name || 'Government of Karnataka');
        const min = b.ministry_name && b.ministry_name !== b.dept_name ? escapeHtml(b.ministry_name) : '';
        const city = escapeHtml(b.consignee_city || 'Bangalore Urban');
        const state = escapeHtml(b.consignee_state || 'KARNATAKA');
        const endFormatted = b.end_date
          ? new Date(b.end_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
          : '16 Nov 2026, 03:00 PM';

        return `
          <tr class="hover:bg-slate-900/70 transition bg-slate-950/40">
            <td class="py-3.5 px-4 font-mono font-bold text-white whitespace-nowrap align-top">
              <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-red-500"></span>
                <span class="select-all tracking-tight">${b.bid_number}</span>
                <button onclick="copyToClipboard('${b.bid_number}')" class="text-slate-500 hover:text-slate-300 p-1" title="Copy Tender No">
                  <i class="fa-regular fa-copy text-[10px]"></i>
                </button>
              </div>
              <span class="inline-block mt-1 px-1.5 py-0.2 rounded text-[9px] font-black bg-red-600/20 text-red-400 border border-red-500/30">MATCH</span>
            </td>
            
            <td class="py-3.5 px-4 align-top">
              <div class="font-bold text-slate-100 flex items-center gap-1.5">
                <i class="fa-solid fa-building text-[11px] text-sky-400 flex-shrink-0"></i>
                <span class="line-clamp-2">${dept}</span>
              </div>
              ${min ? `<div class="text-[11px] text-slate-400 mt-0.5 line-clamp-1">${min}</div>` : ''}
            </td>

            <td class="py-3.5 px-4 align-top">
              <div class="font-semibold text-slate-200 line-clamp-2">${cat}</div>
            </td>

            <td class="py-3.5 px-4 whitespace-nowrap align-top">
              <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-300 border border-slate-800 text-[11px]">
                <i class="fa-solid fa-location-dot text-red-400"></i>
                ${city}
              </span>
            </td>

            <td class="py-3.5 px-4 whitespace-nowrap font-mono text-xs align-top">
              <div class="flex items-center gap-1.5 text-amber-300 font-bold">
                <i class="fa-solid fa-clock text-[10px] text-amber-400"></i>
                <span>${endFormatted}</span>
              </div>
            </td>

            <td class="py-3.5 px-4 text-right whitespace-nowrap align-top">
              <a href="${b.bid_url}" target="_blank" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition shadow-sm">
                <i class="fa-solid fa-file-pdf"></i>
                <span>Open PDF</span>
              </a>
            </td>
          </tr>
        `;
      }).join('');
    }

    function copyToClipboard(text) {
      navigator.clipboard.writeText(text);
      const toast = document.createElement('div');
      toast.className = 'fixed bottom-5 right-5 px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-bold shadow-xl z-50';
      toast.textContent = `Copied ${text} to clipboard!`;
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 2000);
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

    async function triggerManualScan() {
      const icon = document.getElementById('scanIcon');
      icon.classList.add('fa-spin');
      try {
        await fetch('/health/trigger-poll', { method: 'POST' });
        setTimeout(loadDashboardData, 1500);
      } catch (e) {
        console.error(e);
      } finally {
        setTimeout(() => icon.classList.remove('fa-spin'), 1500);
      }
    }

    // --- AUTO-REFRESH TIMER LOOP ---
    setInterval(() => {
      countdownSecs--;
      if (countdownSecs <= 0) {
        countdownSecs = 15;
        loadDashboardData();
      }
      const el = document.getElementById('refreshTimer');
      if (el) el.textContent = `${countdownSecs}s`;
    }, 1000);

    // Initial load
    document.addEventListener('DOMContentLoaded', loadDashboardData);
  </script>
</body>
</html>
"""
