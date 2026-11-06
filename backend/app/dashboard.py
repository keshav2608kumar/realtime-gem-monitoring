"""
GeM BidWatch - Production-Grade Executive Web Dashboard
Enterprise dark-theme UI with real-time tender feeds, audio alarm synthesis,
search profiles, manual scan controls, interactive rule editing, and direct official GeM PDF integration.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GeM BidWatch — Enterprise 24/7 Tender Monitor & Red Alert System</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🚨</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
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
              850: '#151c2e',
              925: '#0d1322',
              950: '#080d19',
            }
          }
        }
      }
    }
  </script>
  <style>
    @keyframes pulse-ring {
      0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
      70% { transform: scale(1); box-shadow: 0 0 0 14px rgba(239, 68, 68, 0); }
      100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    .pulse-alarm { animation: pulse-ring 1.5s infinite cubic-bezier(0.4, 0, 0.6, 1); }
    @keyframes glow-border {
      0%, 100% { border-color: rgba(239, 68, 68, 0.8); box-shadow: 0 0 25px rgba(239, 68, 68, 0.35); }
      50% { border-color: rgba(244, 63, 94, 0.3); box-shadow: 0 0 10px rgba(244, 63, 94, 0.15); }
    }
    .glowing-alert { animation: glow-border 1.2s infinite ease-in-out; }
    .glass-panel {
      background: rgba(17, 24, 39, 0.75);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.07);
    }
    .custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.6); }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(100, 116, 139, 0.4); border-radius: 9999px; }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.7); }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans flex flex-col antialiased selection:bg-red-500 selection:text-white">

  <!-- TOP EXECUTIVE NAVBAR -->
  <header class="border-b border-slate-800/80 bg-slate-925/90 sticky top-0 z-40 backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      
      <!-- Brand & Status Beacon -->
      <div class="flex items-center space-x-3 sm:space-x-4">
        <div class="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-red-600 to-rose-500 shadow-lg shadow-red-950/60 text-white font-black text-lg">
          <i class="fa-solid fa-radar animate-spin" style="animation-duration: 8s;"></i>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <h1 class="text-base sm:text-lg font-black tracking-tight text-white">
              GeM <span class="text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-rose-400">BidWatch</span>
            </h1>
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <span class="w-1.5 h-1.5 mr-1.5 rounded-full bg-emerald-400 animate-ping"></span>
              24/7 ONLINE
            </span>
          </div>
          <p class="text-[11px] text-slate-400 hidden sm:block">Automated Government e-Marketplace Monitoring &amp; Emergency Alert System</p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center space-x-2 sm:space-x-3">
        <button id="btnScan" onclick="triggerManualScan()" class="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 flex items-center gap-2 transition shadow-sm">
          <i class="fa-solid fa-rotate text-sky-400" id="scanIcon"></i>
          <span class="hidden sm:inline">Scan GeM Now</span>
        </button>

        <button onclick="testWebAlarm()" class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white shadow-lg shadow-red-900/40 flex items-center gap-1.5 transition">
          <i class="fa-solid fa-bell animate-pulse"></i>
          <span>Test Alarm Sound</span>
        </button>

        <a href="https://github.com/keshav2608kumar/realtime-gem-monitoring/releases/download/v1.0.0/GeM_BidWatch.apk" class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/30 hidden md:flex items-center gap-1.5 transition">
          <i class="fa-brands fa-android text-sm"></i>
          <span>Download Android APK</span>
        </a>

        <a href="/docs" target="_blank" class="p-2 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition" title="Swagger Interactive API Docs">
          <i class="fa-solid fa-code"></i>
        </a>
      </div>
    </div>
  </header>

  <!-- MAIN BODY -->
  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">

    <!-- METRICS CARDS -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      
      <!-- Metric 1: System Health -->
      <div class="glass-panel rounded-2xl p-4 sm:p-5 flex items-center space-x-4 border border-slate-800">
        <div class="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 text-xl flex-shrink-0">
          <i class="fa-solid fa-shield-halved"></i>
        </div>
        <div class="min-w-0">
          <p class="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Cloud Engine</p>
          <p id="statHealth" class="text-base sm:text-lg font-black text-emerald-400 truncate">24/7 Active</p>
          <p id="statPollSchedule" class="text-[11px] text-slate-500">Scheduled: 300s</p>
        </div>
      </div>

      <!-- Metric 2: Target Location -->
      <div class="glass-panel rounded-2xl p-4 sm:p-5 flex items-center space-x-4 border border-slate-800">
        <div class="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 text-xl flex-shrink-0">
          <i class="fa-solid fa-location-crosshairs"></i>
        </div>
        <div class="min-w-0">
          <p class="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Target Region</p>
          <p id="statRegion" class="text-base sm:text-lg font-black text-white truncate">Bangalore Urban</p>
          <p id="statState" class="text-[11px] text-slate-500 truncate">KARNATAKA, India</p>
        </div>
      </div>

      <!-- Metric 3: Active Keywords -->
      <div class="glass-panel rounded-2xl p-4 sm:p-5 flex items-center space-x-4 border border-slate-800">
        <div class="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 text-xl flex-shrink-0">
          <i class="fa-solid fa-tags"></i>
        </div>
        <div class="min-w-0">
          <p class="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Target Products</p>
          <p id="statKeywords" class="text-sm font-black text-amber-300 truncate">Toner, Printer, Ink</p>
          <p class="text-[11px] text-slate-500 truncate">Cartridge &amp; Consumables</p>
        </div>
      </div>

      <!-- Metric 4: Alerts Count -->
      <div class="glass-panel rounded-2xl p-4 sm:p-5 flex items-center space-x-4 border border-slate-800">
        <div class="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 text-xl flex-shrink-0">
          <i class="fa-solid fa-triangle-exclamation"></i>
        </div>
        <div class="min-w-0">
          <p class="text-[11px] uppercase font-bold text-slate-400 tracking-wider">Fired Alerts</p>
          <p id="statAlerts" class="text-xl sm:text-2xl font-black text-rose-400">0</p>
          <p id="statBidsCount" class="text-[11px] text-slate-500 truncate">0 Tracked in DB</p>
        </div>
      </div>
    </div>

    <!-- ACTIVE TARGET ALERT TOP BANNER -->
    <div id="activeAlertBanner" class="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-red-950/90 via-slate-900 to-red-950/90 border-2 border-red-500/60 shadow-xl shadow-red-950/50 flex flex-col md:flex-row md:items-center justify-between gap-4 glowing-alert hidden">
      <div class="flex items-start sm:items-center gap-3.5">
        <div class="w-12 h-12 rounded-xl bg-red-600 text-white flex items-center justify-center text-xl flex-shrink-0 shadow-lg shadow-red-600/50 animate-pulse">
          <i class="fa-solid fa-bell"></i>
        </div>
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-black bg-red-600 text-white tracking-wider uppercase">
              🚨 ACTIVE TARGET ALERT
            </span>
            <span id="bannerBidNo" class="font-mono font-bold text-white text-sm">GEM/2026/B/8123875</span>
            <span id="bannerKeywords" class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">printer</span>
          </div>
          <p id="bannerCategory" class="text-sm text-slate-100 font-bold mt-1">Computer Printer (V2)</p>
          <div class="flex flex-wrap items-center gap-3 sm:gap-4 text-xs text-slate-400 mt-1">
            <span><i class="fa-solid fa-location-dot text-red-400 mr-1"></i> <span id="bannerLocation" class="text-slate-300">Bangalore Urban, KARNATAKA</span></span>
            <span class="text-amber-300 font-bold"><i class="fa-solid fa-clock text-amber-400 mr-1"></i> Deadline: <span id="bannerDeadline">20 Nov 2026, 05:00 PM</span></span>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-2 self-end md:self-center">
        <button onclick="triggerWebAlarm(currentAlert)" class="px-4 py-2 rounded-xl text-xs font-bold bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-950/50 flex items-center gap-1.5 transition">
          <i class="fa-solid fa-volume-high"></i>
          <span>Sound Siren</span>
        </button>
        <a id="bannerDocLink" href="https://bidplus.gem.gov.in/showbidDocument/9993172" target="_blank" class="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-950/50 flex items-center gap-1.5 transition">
          <i class="fa-solid fa-file-pdf"></i>
          <span>Open GeM PDF</span>
        </a>
      </div>
    </div>

    <!-- TABS NAVIGATION -->
    <div class="flex items-center justify-between border-b border-slate-800/80">
      <div class="flex space-x-4 sm:space-x-8 text-xs sm:text-sm font-bold">
        <button onclick="switchTab('tabFeed')" id="btnTabFeed" class="pb-3 border-b-2 border-red-500 text-red-400 flex items-center gap-2">
          <i class="fa-solid fa-list-check"></i>
          <span>Live Tenders Feed</span>
        </button>
        <button onclick="switchTab('tabProfiles')" id="btnTabProfiles" class="pb-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2">
          <i class="fa-solid fa-sliders"></i>
          <span>Monitoring Rules &amp; Config</span>
        </button>
        <button onclick="switchTab('tabApp')" id="btnTabApp" class="pb-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2">
          <i class="fa-brands fa-android"></i>
          <span>Android App (APK)</span>
        </button>
      </div>

      <div class="text-[11px] text-slate-400 hidden sm:flex items-center gap-2 pb-2">
        <span>Auto-sync in <strong id="refreshTimer" class="text-slate-200 font-mono">15s</strong></span>
        <button onclick="loadAllData()" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition" title="Refresh Now">
          <i class="fa-solid fa-rotate-right"></i>
        </button>
      </div>
    </div>

    <!-- TAB 1: LIVE TENDERS FEED -->
    <section id="tabFeed" class="space-y-4">
      
      <!-- Filter Toolbar -->
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="relative w-full sm:w-96">
          <i class="fa-solid fa-magnifying-glass absolute left-3.5 top-3 text-slate-500 text-xs"></i>
          <input type="text" id="searchInput" oninput="filterBids()" placeholder="Filter by Tender #, Category, Department, City..." class="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition shadow-inner">
        </div>

        <div class="flex items-center space-x-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <button onclick="setKeywordFilter('')" class="filter-btn px-3 py-1 rounded-lg text-xs font-semibold bg-red-600 text-white shadow-md shadow-red-600/30" data-kw="">All</button>
          <button onclick="setKeywordFilter('printer')" class="filter-btn px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700" data-kw="printer">Printers</button>
          <button onclick="setKeywordFilter('toner')" class="filter-btn px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700" data-kw="toner">Toners</button>
          <button onclick="setKeywordFilter('cartridge')" class="filter-btn px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700" data-kw="cartridge">Cartridges</button>
          <button onclick="setKeywordFilter('ink')" class="filter-btn px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700" data-kw="ink">Ink</button>
        </div>
      </div>

      <!-- Tenders Table -->
      <div class="glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-900/90 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-bold">
              <tr>
                <th class="py-3.5 px-4">Tender / Bid Number</th>
                <th class="py-3.5 px-4">Item / Service Category</th>
                <th class="py-3.5 px-4">Delivery Location</th>
                <th class="py-3.5 px-4">Bid End Date / Deadline</th>
                <th class="py-3.5 px-4 text-right">Official Document</th>
              </tr>
            </thead>
            <tbody id="bidsTableBody" class="divide-y divide-slate-800/60 font-medium">
              <tr>
                <td colspan="5" class="py-16 text-center text-slate-500">
                  <i class="fa-solid fa-spinner fa-spin text-2xl text-red-500 mb-3 block"></i>
                  <p class="font-semibold text-slate-300">Connecting to GeM BidWatch engine...</p>
                  <p class="text-[11px] text-slate-500 mt-1">Retrieving latest matched tenders from database</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 2: PROFILES & RULES (INTERACTIVE CONFIGURATION) -->
    <section id="tabProfiles" class="space-y-4 hidden">
      <div class="glass-panel rounded-2xl p-6 border border-slate-800 space-y-5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <h2 class="text-base font-bold text-white flex items-center gap-2">
              <i class="fa-solid fa-sliders text-rose-400"></i>
              Active GeM Monitoring Rules &amp; Targets
            </h2>
            <p class="text-xs text-slate-400 mt-0.5">Edit locations, category keywords, or poll intervals. System applies changes immediately without restarting.</p>
          </div>
          <button onclick="openAddProfileModal()" class="px-4 py-2 rounded-xl text-xs font-bold bg-sky-600 hover:bg-sky-500 text-white flex items-center gap-1.5 transition self-start sm:self-auto shadow-md shadow-sky-900/40">
            <i class="fa-solid fa-plus"></i>
            <span>Add New Rule</span>
          </button>
        </div>

        <!-- Success Toast -->
        <div id="ruleSuccessToast" class="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center gap-2 hidden">
          <i class="fa-solid fa-circle-check"></i>
          <span id="ruleSuccessMsg">Configuration saved successfully! 24/7 Monitor re-synced.</span>
        </div>

        <div id="profilesList" class="space-y-4">
          <!-- Dynamically populated -->
        </div>
      </div>
    </section>

    <!-- TAB 3: ANDROID APK HUB -->
    <section id="tabApp" class="space-y-4 hidden">
      <div class="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h2 class="text-lg font-black text-white flex items-center gap-2">
              <i class="fa-brands fa-android text-emerald-400 text-2xl"></i>
              GeM BidWatch Android App v1.0.0
            </h2>
            <p class="text-xs text-slate-400 mt-1">Get high-priority ambulance-style sirens &amp; full-screen red alerts even when phone screen is locked.</p>
          </div>
          <a href="https://github.com/keshav2608kumar/realtime-gem-monitoring/releases/download/v1.0.0/GeM_BidWatch.apk" class="px-5 py-3 rounded-xl text-sm font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/40 flex items-center gap-2 transition">
            <i class="fa-solid fa-download"></i>
            <span>Download APK (Release v1.0.0)</span>
          </a>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
            <span class="w-7 h-7 rounded-full bg-red-500/20 text-red-400 font-bold flex items-center justify-center text-xs mb-3">1</span>
            <h3 class="text-sm font-bold text-white mb-1">Install on Phone</h3>
            <p class="text-xs text-slate-400">Download <code class="text-amber-300 font-mono text-[11px]">GeM_BidWatch.apk</code> on your Android phone and tap Install. Allow "Install from Unknown Sources" if prompted.</p>
          </div>
          <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
            <span class="w-7 h-7 rounded-full bg-sky-500/20 text-sky-400 font-bold flex items-center justify-center text-xs mb-3">2</span>
            <h3 class="text-sm font-bold text-white mb-1">Pre-configured URL</h3>
            <p class="text-xs text-slate-400">The app automatically connects to this cloud instance (<code class="text-sky-300 font-mono text-[11px]">https://realtime-gem-monitoring.onrender.com</code>). Zero configuration needed.</p>
          </div>
          <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
            <span class="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-400 font-bold flex items-center justify-center text-xs mb-3">3</span>
            <h3 class="text-sm font-bold text-white mb-1">Battery Unrestricted</h3>
            <p class="text-xs text-slate-400">Go to Android Settings &gt; Apps &gt; GeM BidWatch &gt; Battery &gt; Set to <strong>"Unrestricted"</strong> so alarms ring even when locked.</p>
          </div>
        </div>
      </div>
    </section>

  </main>

  <!-- FOOTER -->
  <footer class="border-t border-slate-800/80 bg-slate-925 py-4 text-xs text-slate-500">
    <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
      <p>GeM BidWatch &bull; Continuous 24/7 Monitoring Engine for Government e-Marketplace (GeM India)</p>
      <p class="font-mono text-slate-600">Enterprise Edition v1.0.0</p>
    </div>
  </footer>

  <!-- FULL SCREEN RED ALERT MODAL (SIREN & DIALOG) -->
  <div id="redAlertModal" class="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 hidden">
    <div class="max-w-md w-full bg-gradient-to-b from-red-950 via-slate-900 to-slate-950 border-2 border-red-500 rounded-3xl p-6 shadow-2xl shadow-red-900/60 text-center relative overflow-hidden glowing-alert">
      
      <!-- Pulsing Beacon -->
      <div class="inline-block p-4 rounded-full bg-red-500/20 text-red-500 border-2 border-red-500 pulse-alarm mb-3">
        <i class="fa-solid fa-triangle-exclamation text-4xl"></i>
      </div>

      <div>
        <span class="px-3 py-1 rounded-full text-[10px] font-black tracking-widest bg-red-600 text-white uppercase shadow-lg shadow-red-600/40">
          🚨 GeM EMERGENCY ALARM
        </span>
        <h3 class="text-xl sm:text-2xl font-black text-white mt-2">MATCHING TENDER DETECTED!</h3>
        <p id="modalLocation" class="text-xs text-slate-300 font-semibold mt-1">Bangalore Urban, KARNATAKA</p>
      </div>

      <!-- Tender Info Box -->
      <div class="bg-slate-950/80 rounded-2xl p-4 text-left border border-red-900/40 space-y-3 mt-4">
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Tender / Bid Number</span>
          <p id="modalBidNo" class="text-lg font-black text-white font-mono select-all">GEM/2026/B/8123875</p>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Matched Keywords</span>
          <div>
            <span id="modalKeywords" class="px-2 py-0.5 rounded-md text-xs font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30">
              printer, toner
            </span>
          </div>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Category</span>
          <p id="modalCategory" class="text-xs sm:text-sm font-semibold text-slate-200">Computer Printer (V2) / Toner Cartridges</p>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Delivery Location</span>
          <p id="modalDelivery" class="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <i class="fa-solid fa-location-dot text-red-400"></i>
            <span>Bangalore Urban, KARNATAKA</span>
          </p>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Bid End Date / Deadline</span>
          <p id="modalEndDate" class="text-xs sm:text-sm font-bold text-amber-300 flex items-center gap-1.5">
            <i class="fa-solid fa-clock text-amber-400"></i>
            <span id="modalEndDateVal">20 Nov 2026, 05:00 PM</span>
          </p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="space-y-2 pt-4">
        <a id="modalDocLink" href="https://bidplus.gem.gov.in/showbidDocument/9993172" target="_blank" class="w-full py-3 rounded-xl text-sm font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/50 transition">
          <i class="fa-solid fa-file-pdf text-base"></i>
          <span>Open Official GeM Bid Document (PDF)</span>
        </a>
        <button onclick="silenceWebAlarm()" class="w-full py-2.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition">
          <i class="fa-solid fa-volume-xmark mr-1"></i> Silence Alarm &amp; Close
        </button>
      </div>

    </div>
  </div>

  <!-- EDIT / ADD PROFILE MODAL -->
  <div id="profileEditModal" class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 hidden">
    <div class="max-w-lg w-full bg-slate-900 border border-slate-700 rounded-3xl p-6 shadow-2xl space-y-4">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 id="modalProfileTitle" class="text-base font-bold text-white flex items-center gap-2">
          <i class="fa-solid fa-sliders text-sky-400"></i>
          Edit Monitoring Rule
        </h3>
        <button onclick="closeProfileModal()" class="text-slate-400 hover:text-white p-1">
          <i class="fa-solid fa-xmark text-lg"></i>
        </button>
      </div>

      <form id="profileForm" onsubmit="saveProfileForm(event)" class="space-y-3.5 text-xs">
        <input type="hidden" id="formProfileId" value="">

        <div>
          <label class="block font-bold text-slate-300 mb-1">Rule Name</label>
          <input type="text" id="formProfileName" required class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-sky-500" placeholder="e.g. Bangalore - Toner & Printer">
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-bold text-slate-300 mb-1">Target State</label>
            <input type="text" id="formProfileState" required class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-sky-500" placeholder="KARNATAKA">
          </div>
          <div>
            <label class="block font-bold text-slate-300 mb-1">Polling Interval (Seconds)</label>
            <input type="number" id="formProfileInterval" min="60" step="30" required class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-sky-500" placeholder="300">
          </div>
        </div>

        <div>
          <label class="block font-bold text-slate-300 mb-1">Target Cities (Comma-separated)</label>
          <input type="text" id="formProfileCities" required class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-sky-500" placeholder="BANGALORE, Bangalore Urban, BENGALURU URBAN, Bengaluru">
          <p class="text-[10px] text-slate-500 mt-1">Include all spelling variations used on GeM.</p>
        </div>

        <div>
          <label class="block font-bold text-slate-300 mb-1">Target Keywords (Comma-separated)</label>
          <input type="text" id="formProfileKeywords" required class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-sky-500" placeholder="toner, cartridge, printer, ink">
          <p class="text-[10px] text-slate-500 mt-1">Whole word matching protects against false positives.</p>
        </div>

        <div class="flex items-center gap-2 pt-1">
          <input type="checkbox" id="formProfileActive" checked class="w-4 h-4 rounded text-sky-600 bg-slate-950 border-slate-800 focus:ring-sky-500">
          <label for="formProfileActive" class="font-bold text-slate-300">Active Monitoring (triggers sirens &amp; alerts)</label>
        </div>

        <div class="flex justify-end gap-2 pt-3 border-t border-slate-800">
          <button type="button" onclick="closeProfileModal()" class="px-4 py-2 rounded-xl font-bold bg-slate-800 hover:bg-slate-700 text-slate-300 transition">Cancel</button>
          <button type="submit" id="btnSaveProfile" class="px-5 py-2 rounded-xl font-bold bg-sky-600 hover:bg-sky-500 text-white transition flex items-center gap-1.5 shadow-md shadow-sky-900/50">
            <i class="fa-solid fa-check"></i>
            <span>Save &amp; Apply Changes</span>
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- JAVASCRIPT CONTROLLER -->
  <script>
    let allBids = [];
    let allProfiles = [];
    let currentAlert = null;
    let activeKwFilter = '';
    let audioCtx = null;
    let alarmOsc = null;
    let alarmGain = null;
    let sirenInterval = null;
    let timerCount = 15;

    // --- TAB SWITCHING ---
    function switchTab(tabId) {
      ['tabFeed', 'tabProfiles', 'tabApp'].forEach(id => {
        document.getElementById(id).classList.add('hidden');
      });
      ['btnTabFeed', 'btnTabProfiles', 'btnTabApp'].forEach(id => {
        document.getElementById(id).className = "pb-3 border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2 transition";
      });

      document.getElementById(tabId).classList.remove('hidden');
      if (tabId === 'tabFeed') document.getElementById('btnTabFeed').className = "pb-3 border-b-2 border-red-500 text-red-400 flex items-center gap-2";
      if (tabId === 'tabProfiles') document.getElementById('btnTabProfiles').className = "pb-3 border-b-2 border-red-500 text-red-400 flex items-center gap-2";
      if (tabId === 'tabApp') document.getElementById('btnTabApp').className = "pb-3 border-b-2 border-red-500 text-red-400 flex items-center gap-2";
    }

    // --- LOAD DATA FROM CLOUD REST API IN PARALLEL ---
    async function loadAllData() {
      try {
        const [hRes, pRes, aRes, bRes] = await Promise.allSettled([
          fetch('/health/').then(r => r.ok ? r.json() : null),
          fetch('/profiles/').then(r => r.ok ? r.json() : null),
          fetch('/alerts/?limit=100').then(r => r.ok ? r.json() : null),
          fetch('/bids/?limit=100').then(r => r.ok ? r.json() : null)
        ]);

        // 1. Health
        if (hRes.status === 'fulfilled' && hRes.value) {
          const h = hRes.value;
          const elHealth = document.getElementById('statHealth');
          if (elHealth) elHealth.textContent = h.monitor_running ? '24/7 Active' : 'Paused';
          const elBidsCount = document.getElementById('statBidsCount');
          if (elBidsCount) elBidsCount.textContent = `${h.total_bids_in_db || 0} Tracked in DB`;
        }

        // 2. Profiles
        if (pRes.status === 'fulfilled' && pRes.value) {
          allProfiles = pRes.value;
          renderProfiles(allProfiles);
          if (allProfiles.length > 0) {
            const p = allProfiles[0];
            const elRegion = document.getElementById('statRegion');
            if (elRegion) elRegion.textContent = Array.isArray(p.cities) ? p.cities[0] : (p.cities || 'Bangalore');
            const elState = document.getElementById('statState');
            if (elState) elState.textContent = `${p.state || 'KARNATAKA'}, India`;
            const elKw = document.getElementById('statKeywords');
            if (elKw && Array.isArray(p.keywords)) {
              elKw.textContent = p.keywords.slice(0, 3).map(k => k.charAt(0).toUpperCase() + k.slice(1)).join(', ');
            }
          }
        }

        // 3. Alerts
        if (aRes.status === 'fulfilled' && aRes.value) {
          const alerts = aRes.value;
          const elAlerts = document.getElementById('statAlerts');
          if (elAlerts) elAlerts.textContent = alerts.length;
          
          if (alerts.length > 0) {
            currentAlert = alerts[0];
            renderTopAlertBanner(currentAlert);
          } else {
            const banner = document.getElementById('activeAlertBanner');
            if (banner) banner.classList.add('hidden');
          }
        }

        // 4. Bids (Preserves User Filter Synchronously!)
        if (bRes.status === 'fulfilled' && bRes.value) {
          allBids = bRes.value;
          filterBids();
        } else {
          // Fallback if bids failed
          if (allBids.length === 0) {
            const tbody = document.getElementById('bidsTableBody');
            if (tbody) {
              tbody.innerHTML = `
                <tr>
                  <td colspan="5" class="py-14 text-center text-slate-400">
                    <i class="fa-solid fa-cloud-arrow-down text-2xl text-amber-400 mb-2 block"></i>
                    <p class="font-bold text-slate-200">Connecting to GeM Database...</p>
                    <p class="text-xs text-slate-500 mt-1">Auto-refreshing in 3 seconds or click "Scan GeM Now".</p>
                  </td>
                </tr>
              `;
            }
          }
        }
      } catch (err) {
        console.error('Data sync error:', err);
      }
    }

    function renderTopAlertBanner(alert) {
      if (!alert) return;
      const b = alert.bid || {};
      const banner = document.getElementById('activeAlertBanner');
      if (!banner) return;

      document.getElementById('bannerBidNo').textContent = b.bid_number || 'GEM/2026/B/8123875';
      document.getElementById('bannerCategory').textContent = b.category_name || 'Computer Printer (V2)';
      document.getElementById('bannerKeywords').textContent = alert.matched_keywords || 'printer';
      document.getElementById('bannerLocation').textContent = `${b.consignee_city || 'Bangalore Urban'}, ${b.consignee_state || 'KARNATAKA'}`;
      
      const deadline = b.end_date 
        ? new Date(b.end_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
        : '20 Nov 2026, 05:00 PM';
      document.getElementById('bannerDeadline').textContent = deadline;

      if (b.bid_url) {
        document.getElementById('bannerDocLink').href = b.bid_url;
      }
      banner.classList.remove('hidden');
    }

    function renderBids(bids) {
      const tbody = document.getElementById('bidsTableBody');
      if (!bids || bids.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" class="py-14 text-center text-slate-400">
              <i class="fa-solid fa-filter-circle-xmark text-3xl mb-2 text-slate-600 block"></i>
              <p class="font-bold text-slate-300">No tenders match category "${escapeHtml(activeKwFilter || 'selected filter')}"</p>
              <p class="text-xs text-slate-500 mt-1 max-w-md mx-auto">Click <button onclick="setKeywordFilter('')" class="text-red-400 font-bold underline">"All"</button> to view all active listings, or click "Scan GeM Now".</p>
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = bids.map(b => {
        const cat = escapeHtml(b.category_name);
        const city = escapeHtml(b.consignee_city || 'Bangalore');
        const state = escapeHtml(b.consignee_state || 'KARNATAKA');
        const isMatched = /printer|toner|cartridge|ink/i.test(cat);

        const endFormatted = b.end_date 
          ? new Date(b.end_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
          : '20 Nov 2026, 05:00 PM';

        return `
          <tr class="hover:bg-slate-900/60 transition ${isMatched ? 'bg-red-950/20 border-l-2 border-red-500' : ''}">
            <td class="py-3.5 px-4 font-mono font-bold text-white whitespace-nowrap">
              <div class="flex items-center gap-1.5">
                ${isMatched ? '<span class="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>' : ''}
                <span class="select-all">${b.bid_number}</span>
                ${isMatched ? '<span class="ml-1.5 px-1.5 py-0.5 rounded text-[9px] font-black bg-red-600/30 text-red-400 border border-red-500/40">MATCH</span>' : ''}
              </div>
            </td>
            <td class="py-3.5 px-4 text-slate-200">
              <div class="font-semibold max-w-md ${isMatched ? 'text-white' : ''}">${cat}</div>
            </td>
            <td class="py-3.5 px-4 text-slate-300 whitespace-nowrap">
              <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-300 border border-slate-800 text-[11px]">
                <i class="fa-solid fa-location-dot text-red-400"></i>
                ${city}, ${state}
              </span>
            </td>
            <td class="py-3.5 px-4 whitespace-nowrap font-mono text-xs">
              <div class="flex items-center gap-1.5 ${isMatched ? 'text-amber-300 font-bold' : 'text-slate-400'}">
                <i class="fa-solid fa-clock text-[10px] ${isMatched ? 'text-amber-400' : 'text-slate-500'}"></i>
                <span>${endFormatted}</span>
              </div>
            </td>
            <td class="py-3.5 px-4 text-right whitespace-nowrap">
              <a href="${b.bid_url}" target="_blank" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition shadow-sm">
                <i class="fa-solid fa-file-pdf"></i>
                <span>Open PDF</span>
              </a>
            </td>
          </tr>
        `;
      }).join('');
    }

    function renderProfiles(profiles) {
      const container = document.getElementById('profilesList');
      if (!profiles || profiles.length === 0) {
        container.innerHTML = `<p class="text-xs text-slate-500">No active rules configured. Click "Add New Rule" above to create one.</p>`;
        return;
      }
      container.innerHTML = profiles.map(p => {
        const citiesList = Array.isArray(p.cities) ? p.cities : (p.cities ? [p.cities] : ['All Cities']);
        const keywordsList = Array.isArray(p.keywords) ? p.keywords : (p.keywords ? [p.keywords] : []);
        const pJson = JSON.stringify(p).replace(/"/g, '&quot;');

        return `
        <div class="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-bold text-white">${escapeHtml(p.name)}</h3>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${p.is_active ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-slate-700 text-slate-400'}">
                ${p.is_active ? 'ACTIVE' : 'PAUSED'}
              </span>
            </div>
            <p class="text-xs text-slate-400">
              <strong>State:</strong> <span class="text-slate-200">${escapeHtml(p.state || 'All')}</span> &bull; 
              <strong>Cities:</strong> <span class="text-slate-200">${escapeHtml(citiesList.join(', '))}</span>
            </p>
            <div class="flex flex-wrap gap-1.5 pt-1">
              ${keywordsList.map(k => `<span class="px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">${escapeHtml(k)}</span>`).join('')}
            </div>
          </div>
          
          <div class="flex items-center gap-2 self-start md:self-center">
            <button onclick="toggleProfileActive(${p.id}, ${!p.is_active})" class="px-3 py-1.5 rounded-xl text-xs font-bold ${p.is_active ? 'bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'} transition flex items-center gap-1.5">
              <i class="fa-solid ${p.is_active ? 'fa-pause' : 'fa-play'}"></i>
              <span>${p.is_active ? 'Pause Rule' : 'Activate Rule'}</span>
            </button>
            <button onclick="openEditProfileModal(${pJson})" class="px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-1.5">
              <i class="fa-solid fa-pen-to-square"></i>
              <span>Edit Rule</span>
            </button>
          </div>
        </div>
        `;
      }).join('');
    }

    async function toggleProfileActive(id, newStatus) {
      try {
        const res = await fetch(`/profiles/${id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ is_active: newStatus })
        });
        if (res.ok) {
          showToast(`Rule status changed to ${newStatus ? 'ACTIVE' : 'PAUSED'}.`);
          loadAllData();
        }
      } catch (e) {
        alert('Failed to update status: ' + e);
      }
    }

    function openEditProfileModal(p) {
      document.getElementById('modalProfileTitle').innerHTML = '<i class="fa-solid fa-pen-to-square text-sky-400 mr-2"></i> Edit Monitoring Rule';
      document.getElementById('formProfileId').value = p.id;
      document.getElementById('formProfileName').value = p.name;
      document.getElementById('formProfileState').value = p.state || 'KARNATAKA';
      document.getElementById('formProfileInterval').value = p.poll_interval_seconds || 300;
      
      const citiesList = Array.isArray(p.cities) ? p.cities.join(', ') : (p.cities || '');
      document.getElementById('formProfileCities').value = citiesList;

      const kwList = Array.isArray(p.keywords) ? p.keywords.join(', ') : (p.keywords || '');
      document.getElementById('formProfileKeywords').value = kwList;

      document.getElementById('formProfileActive').checked = p.is_active !== false;

      document.getElementById('profileEditModal').classList.remove('hidden');
    }

    function openAddProfileModal() {
      document.getElementById('modalProfileTitle').innerHTML = '<i class="fa-solid fa-plus text-sky-400 mr-2"></i> Add New Monitoring Rule';
      document.getElementById('formProfileId').value = '';
      document.getElementById('formProfileName').value = '';
      document.getElementById('formProfileState').value = 'KARNATAKA';
      document.getElementById('formProfileInterval').value = '300';
      document.getElementById('formProfileCities').value = 'BANGALORE, Bangalore Urban, BENGALURU URBAN, Bengaluru';
      document.getElementById('formProfileKeywords').value = 'toner, cartridge, printer, ink';
      document.getElementById('formProfileActive').checked = true;

      document.getElementById('profileEditModal').classList.remove('hidden');
    }

    function closeProfileModal() {
      document.getElementById('profileEditModal').classList.add('hidden');
    }

    async function saveProfileForm(e) {
      e.preventDefault();
      const id = document.getElementById('formProfileId').value;
      const name = document.getElementById('formProfileName').value.trim();
      const state = document.getElementById('formProfileState').value.trim();
      const poll_interval_seconds = parseInt(document.getElementById('formProfileInterval').value) || 300;
      const citiesRaw = document.getElementById('formProfileCities').value;
      const keywordsRaw = document.getElementById('formProfileKeywords').value;
      const is_active = document.getElementById('formProfileActive').checked;

      const cities = citiesRaw.split(',').map(s => s.trim()).filter(Boolean);
      const keywords = keywordsRaw.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);

      const payload = {
        name,
        state,
        poll_interval_seconds,
        cities,
        keywords,
        is_active
      };

      try {
        const url = id ? `/profiles/${id}` : '/profiles/';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          closeProfileModal();
          showToast(`Rule "${name}" successfully saved! Target settings active.`);
          loadAllData();
        } else {
          alert('Failed to save profile: HTTP ' + res.status);
        }
      } catch (err) {
        alert('Network error while saving profile: ' + err);
      }
    }

    function showToast(msg) {
      const toast = document.getElementById('ruleSuccessToast');
      const msgEl = document.getElementById('ruleSuccessMsg');
      if (toast && msgEl) {
        msgEl.textContent = msg;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 4000);
      }
    }

    function setKeywordFilter(kw) {
      activeKwFilter = kw.toLowerCase();
      document.querySelectorAll('.filter-btn').forEach(btn => {
        if (btn.getAttribute('data-kw') === kw) {
          btn.className = "filter-btn px-3 py-1 rounded-lg text-xs font-semibold bg-red-600 text-white shadow-md shadow-red-600/30";
        } else {
          btn.className = "filter-btn px-3 py-1 rounded-lg text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700";
        }
      });
      filterBids();
    }

    function filterBids() {
      const q = (document.getElementById('searchInput').value || '').toLowerCase().trim();
      let filtered = allBids;
      if (activeKwFilter) {
        filtered = filtered.filter(b => (b.category_name || '').toLowerCase().includes(activeKwFilter));
      }
      if (q) {
        filtered = filtered.filter(b => 
          (b.bid_number && b.bid_number.toLowerCase().includes(q)) ||
          (b.category_name && b.category_name.toLowerCase().includes(q)) ||
          (b.consignee_city && b.consignee_city.toLowerCase().includes(q))
        );
      }
      renderBids(filtered);
    }

    async function triggerManualScan() {
      const icon = document.getElementById('scanIcon');
      icon.classList.add('fa-spin');
      try {
        const res = await fetch('/health/trigger-poll', { method: 'POST' });
        if (res.ok) {
          setTimeout(loadAllData, 2500);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setTimeout(() => icon.classList.remove('fa-spin'), 1500);
      }
    }

    // --- WEB AUDIO SIREN SYNTHESIZER ---
    function triggerWebAlarm(alert) {
      const b = (alert && alert.bid) ? alert.bid : {};
      document.getElementById('modalBidNo').textContent = b.bid_number || 'GEM/2026/B/8124901';
      document.getElementById('modalKeywords').textContent = (alert && alert.matched_keywords) ? alert.matched_keywords : 'toner, cartridge';
      document.getElementById('modalCategory').textContent = b.category_name || 'Genuine High-Yield Toner Cartridges';
      document.getElementById('modalLocation').textContent = `${b.consignee_city || 'Bangalore Urban'}, ${b.consignee_state || 'KARNATAKA'}`;
      document.getElementById('modalDelivery').innerHTML = `<i class="fa-solid fa-location-dot text-red-400"></i> <span>${b.consignee_city || 'Bangalore Urban'}, ${b.consignee_state || 'KARNATAKA'}</span>`;
      
      const deadline = b.end_date 
        ? new Date(b.end_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
        : '22 Nov 2026, 03:00 PM';
      document.getElementById('modalEndDateVal').textContent = deadline;

      if (b.bid_url) document.getElementById('modalDocLink').href = b.bid_url;

      document.getElementById('redAlertModal').classList.remove('hidden');
      playLoudSiren();
    }

    function testWebAlarm() {
      triggerWebAlarm(currentAlert);
    }

    function playLoudSiren() {
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
        alarmGain.gain.setValueAtTime(0.35, audioCtx.currentTime);

        alarmOsc.connect(alarmGain);
        alarmGain.connect(audioCtx.destination);
        alarmOsc.start();

        let high = false;
        clearInterval(sirenInterval);
        sirenInterval = setInterval(() => {
          if (!audioCtx) return;
          const targetFreq = high ? 980 : 680;
          alarmOsc.frequency.exponentialRampToValueAtTime(targetFreq, audioCtx.currentTime + 0.15);
          high = !high;
        }, 220);
      } catch (e) {
        console.warn("Audio Context error:", e);
      }
    }

    function silenceWebAlarm() {
      document.getElementById('redAlertModal').classList.add('hidden');
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

    // Auto-refresh timer (every second)
    setInterval(() => {
      timerCount--;
      if (timerCount <= 0) {
        timerCount = 15;
        loadAllData();
      }
      document.getElementById('refreshTimer').textContent = `${timerCount}s`;
    }, 1000);

    // Initial load immediately
    loadAllData();
  </script>
</body>
</html>
"""
