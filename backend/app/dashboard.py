"""
GeM BidWatch — Executive Enterprise Dashboard
Real-time 24/7 Procurement Monitoring with Accurate Administrative Locations,
Timezone-Aware IST Timestamps, Strict Lifecycle Segregation,
7 Dedicated Product Category Filters, and Document-Extracted Delivery Location Intelligence.
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
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #020617; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #334155; }
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
            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">ENTERPRISE v2.5</span>
          </div>
          <p class="text-[11px] text-slate-400 hidden sm:block">Government e-Marketplace High-Accuracy Procurement Radar</p>
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

    <!-- MANDATORY TARGET LOCATION BANNER -->
    <div class="p-3.5 rounded-xl bg-slate-900/95 border border-emerald-500/30 shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 flex-shrink-0">
          <i class="fa-solid fa-location-crosshairs text-base"></i>
        </div>
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-black uppercase tracking-wider text-slate-400">Target Location:</span>
            <span class="px-2.5 py-0.5 rounded text-xs font-mono font-extrabold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">Bengaluru Urban, Karnataka</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-300 border border-blue-500/20 font-mono">Urban PINs: 560001 - 560110</span>
          </div>
          <p class="text-[11px] text-slate-400 mt-0.5">
            Strict geographic filter active: Bids with delivery in Bengaluru Rural, other districts, or outside states are rejected or isolated in the Review Queue.
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2 self-end sm:self-center">
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-950/60 text-emerald-300 border border-emerald-500/30 text-[11px] font-black tracking-wide">
          <i class="fa-solid fa-shield-halved text-xs text-emerald-400"></i>
          <span>BENGALURU URBAN VERIFIED</span>
        </span>
      </div>
    </div>

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
          <p id="statHealthSubtitle" class="text-[10px] text-slate-500 mt-0.5">Bengaluru Urban Radar Active</p>
        </div>
        <div class="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
          <i class="fa-solid fa-server"></i>
        </div>
      </div>

      <!-- Metric 2: Verified Bengaluru Urban Bids in DB -->
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm flex items-center justify-between">
        <div>
          <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Bengaluru Urban Bids</p>
          <p id="statActiveBids" class="text-base sm:text-lg font-black text-emerald-400 font-mono mt-1">-- Verified</p>
          <p id="statTotalBids" class="text-[10px] text-slate-500 mt-0.5">-- Total Tracked</p>
        </div>
        <div class="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
          <i class="fa-solid fa-location-dot"></i>
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

      <!-- Metric 4: Review Queue Count -->
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm flex items-center justify-between">
        <div>
          <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Review Queue</p>
          <p id="statReviewCount" class="text-base sm:text-lg font-black text-amber-400 font-mono mt-1">-- Review</p>
          <p id="statExpiredBids" class="text-[10px] text-slate-500 mt-0.5">-- Expired Excluded</p>
        </div>
        <div class="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
          <i class="fa-solid fa-clipboard-question"></i>
        </div>
      </div>

    </div>

    <!-- DEDICATED PRODUCT CATEGORY FILTER PANEL (FEATURE 1) -->
    <div class="p-4 bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl space-y-3">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2.5">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <i class="fa-solid fa-layer-group text-sm"></i>
          </div>
          <div>
            <h3 class="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <span>Official GeM Product Category Filters</span>
              <span id="selectedCatBadge" class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">7 Selected</span>
            </h3>
            <p class="text-[11px] text-slate-400">Multi-select target GeM categories to narrow live opportunities &amp; radar alerts.</p>
          </div>
        </div>

        <!-- Quick Multi-Select Controls -->
        <div class="flex items-center gap-2 self-end sm:self-center">
          <button onclick="selectAllCategories()" class="px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-1.5">
            <i class="fa-solid fa-check-double text-[10px] text-blue-400"></i>
            <span>Select All</span>
          </button>
          <button onclick="clearAllCategories()" class="px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition flex items-center gap-1.5">
            <i class="fa-solid fa-xmark text-[10px]"></i>
            <span>Clear All</span>
          </button>
        </div>
      </div>

      <!-- 7 Exact Categories Checkbox Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2.5 pt-1" id="categoryCheckboxesContainer">
        <!-- Rendered dynamically via renderCategoryCheckboxes() -->
      </div>

      <!-- Active Filter Summary Bar -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
        <div class="flex items-center gap-1.5 flex-wrap">
          <span class="font-bold text-slate-400 uppercase text-[10px]">Active Filters:</span>
          <div id="activeCategoryChips" class="flex items-center gap-1.5 flex-wrap">
            <!-- Chips rendered dynamically -->
          </div>
        </div>
        <div class="text-[10px] text-slate-500 font-mono">
          <i class="fa-solid fa-database mr-1"></i>Synchronized with Backend Query Engine
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
          
          <!-- Status & Scope Tabs -->
          <div class="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs overflow-x-auto">
            <button onclick="setScopeTab('bengaluru_urban', 'active')" id="tabVerified" class="px-3 py-1.5 rounded-lg font-bold transition bg-emerald-600 text-white shadow flex items-center gap-1.5 whitespace-nowrap">
              <i class="fa-solid fa-circle-check text-[11px]"></i>
              <span>Verified Bengaluru Urban</span>
            </button>
            <button onclick="setScopeTab('review', 'all')" id="tabReview" class="px-3 py-1.5 rounded-lg font-bold transition text-slate-400 hover:text-white flex items-center gap-1.5 whitespace-nowrap">
              <i class="fa-solid fa-triangle-exclamation text-[11px] text-amber-400"></i>
              <span>Review Queue</span>
            </button>
            <button onclick="setScopeTab('bengaluru_urban', 'closing_soon')" id="tabClosingSoon" class="px-3 py-1.5 rounded-lg font-bold transition text-slate-400 hover:text-white flex items-center gap-1.5 whitespace-nowrap">
              <i class="fa-solid fa-hourglass-half text-[11px] text-amber-400"></i>
              <span>Closing Soon (&lt;24h)</span>
            </button>
            <button onclick="setScopeTab('bengaluru_urban', 'expired')" id="tabExpired" class="px-3 py-1.5 rounded-lg font-bold transition text-slate-400 hover:text-white flex items-center gap-1.5 whitespace-nowrap">
              <i class="fa-solid fa-archive text-[11px]"></i>
              <span>Expired Archive</span>
            </button>
            <button onclick="setScopeTab('all', 'all')" id="tabAll" class="px-3 py-1.5 rounded-lg font-bold transition text-slate-400 hover:text-white whitespace-nowrap">
              All Ingested Records
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

        <!-- Row 2: Search Input & Location Scope -->
        <div class="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 pt-1">
          
          <!-- Location Scope Selector -->
          <div class="flex items-center gap-2 text-xs text-slate-400">
            <span class="font-bold text-[10px] uppercase tracking-wider text-slate-500">Location Filter Target:</span>
            <select id="locationTypeSelect" onchange="onLocationTypeChange()" class="px-2.5 py-1 rounded-lg bg-slate-950 text-slate-200 border border-slate-800 text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500">
              <option value="consignee" selected>Consignee / Delivery Address</option>
              <option value="pdf_delivery">PDF Extracted Address Only</option>
              <option value="buyer">Buyer Organization Only</option>
              <option value="any">Any Available Location</option>
            </select>
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
              <th class="py-3 px-4 w-60">Procuring Department</th>
              <th class="py-3 px-4 min-w-[200px]">Item & Category</th>
              <th class="py-3 px-4 w-44">Delivery Location</th>
              <th class="py-3 px-4 w-36">Published Date (IST)</th>
              <th class="py-3 px-4 w-44">Bid Deadline (IST)</th>
              <th class="py-3 px-4 w-32 text-center">Action</th>
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

  <!-- TENDER DETAIL & PDF LOCATION MODAL (FEATURE 2) -->
  <div id="bidDetailModal" class="hidden fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl space-y-4">
      <div class="flex items-start justify-between border-b border-slate-800 pb-3">
        <div>
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-blue-600 text-white">GeM TENDER INTELLIGENCE</span>
            <span id="detailBidStatus" class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300">ACTIVE</span>
          </div>
          <h2 id="detailBidNumber" class="text-lg font-black text-white font-mono mt-1">--</h2>
          <p id="detailCategory" class="text-xs text-slate-300 mt-0.5">--</p>
        </div>
        <button onclick="closeBidDetailModal()" class="text-slate-400 hover:text-white p-1">
          <i class="fa-solid fa-xmark text-lg"></i>
        </button>
      </div>

      <!-- Overview Grid -->
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs">
        <div>
          <span class="text-[10px] font-bold uppercase text-slate-500">Department</span>
          <p id="detailDept" class="font-bold text-slate-200 mt-0.5">--</p>
        </div>
        <div>
          <span class="text-[10px] font-bold uppercase text-slate-500">Ministry</span>
          <p id="detailMinistry" class="font-semibold text-slate-300 mt-0.5">--</p>
        </div>
        <div>
          <span class="text-[10px] font-bold uppercase text-slate-500">Quantity</span>
          <p id="detailQty" class="font-mono font-bold text-slate-200 mt-0.5">--</p>
        </div>
        <div>
          <span class="text-[10px] font-bold uppercase text-slate-500">Published Date</span>
          <p id="detailPubDate" class="font-mono text-slate-300 mt-0.5">--</p>
        </div>
        <div>
          <span class="text-[10px] font-bold uppercase text-slate-500">Bid Deadline</span>
          <p id="detailEndDate" class="font-mono font-bold text-amber-300 mt-0.5">--</p>
        </div>
        <div>
          <span class="text-[10px] font-bold uppercase text-slate-500">Time Remaining</span>
          <p id="detailTimeRem" class="font-semibold text-emerald-400 mt-0.5">--</p>
        </div>
      </div>

      <!-- DEDICATED SECTION: DELIVERY LOCATION — EXTRACTED FROM BID DOCUMENT -->
      <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
        <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-file-shield text-emerald-400 text-sm"></i>
            <h4 class="text-xs font-bold uppercase tracking-wider text-white">DELIVERY LOCATION — EXTRACTED FROM BID DOCUMENT</h4>
          </div>
          <span id="detailPdfStatusBadge" class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">UNKNOWN</span>
        </div>

        <div id="detailPdfContent" class="text-xs space-y-2">
          <!-- Rendered dynamically -->
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center justify-between pt-2">
        <button id="btnTriggerPdfExtract" onclick="runOnDemandPdfExtraction()" class="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-bold flex items-center gap-1.5 transition">
          <i id="extractSpinner" class="fa-solid fa-arrows-rotate text-[11px]"></i>
          <span>Extract / Re-verify from PDF</span>
        </button>
        <div class="flex items-center gap-2">
          <button onclick="closeBidDetailModal()" class="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700">
            Close
          </button>
          <a id="detailPdfLink" href="#" target="_blank" class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold shadow-md shadow-red-600/30 flex items-center gap-1.5">
            <i class="fa-solid fa-file-pdf"></i>
            <span>Open Official PDF</span>
          </a>
        </div>
      </div>
    </div>
  </div>

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
    // 7 Canonical GeM Categories with exact names
    const CANONICAL_CATEGORIES = [
      { id: 'TONER_INK_PRINTER_CONSUMABLES', name: 'Toner Cartridges / Ink Cartridges / Consumables for Printers' },
      { id: 'SCANNER_V3', name: 'Scanner (V3)' },
      { id: 'A4_LEGAL_SIZE_MFP', name: 'A4 and Legal Size Multifunction Printer (MFP)' },
      { id: 'A3_SIZE_MFP', name: 'A3 Size Multifunction Printer (MFP)' },
      { id: 'COMPUTER_PRINTER_V2', name: 'Computer Printer (V2)' },
      { id: 'HIGH_END_DESKTOP', name: 'High End Desktop Computer' },
      { id: 'HIGH_END_LAPTOP_NOTEBOOK', name: 'High End Laptop - Notebook' },
    ];

    // Global State
    let currentScope = 'bengaluru_urban'; // 'bengaluru_urban' (default), 'review', 'all'
    let currentFeedStatus = 'active'; // 'active', 'closing_soon', 'expired', 'all'
    let currentSortBy = 'closing_soonest';
    let currentLocationType = 'consignee';
    let searchQuery = '';
    let allBids = [];
    let activeAlertId = null;
    let currentModalBid = null;

    // Persisted Category Selection (localStorage)
    let selectedCategories = [];
    try {
      const stored = localStorage.getItem('gem_selected_categories');
      if (stored) {
        selectedCategories = JSON.parse(stored);
      } else {
        // Default: all 7 categories selected
        selectedCategories = CANONICAL_CATEGORIES.map(c => c.id);
        localStorage.setItem('gem_selected_categories', JSON.stringify(selectedCategories));
      }
    } catch (e) {
      selectedCategories = CANONICAL_CATEGORIES.map(c => c.id);
    }

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

    // --- CATEGORY FILTER UI CONTROLS (FEATURE 1) ---
    function renderCategoryCheckboxes() {
      const container = document.getElementById('categoryCheckboxesContainer');
      const chipsContainer = document.getElementById('activeCategoryChips');
      const badge = document.getElementById('selectedCatBadge');

      badge.textContent = `${selectedCategories.length} of ${CANONICAL_CATEGORIES.length} Selected`;

      container.innerHTML = CANONICAL_CATEGORIES.map(c => {
        const isChecked = selectedCategories.includes(c.id);
        const borderStyle = isChecked ? 'border-blue-500/50 bg-blue-950/20' : 'border-slate-800 bg-slate-950/40 opacity-75';
        return `
          <label class="flex items-start gap-2.5 p-2.5 rounded-xl border ${borderStyle} hover:border-slate-700 cursor-pointer transition select-none">
            <input type="checkbox" onchange="toggleCategory('${c.id}')" ${isChecked ? 'checked' : ''} class="mt-0.5 rounded border-slate-700 text-blue-600 focus:ring-0 focus:ring-offset-0 bg-slate-900 cursor-pointer w-4 h-4">
            <div class="leading-tight">
              <span class="text-xs font-bold text-slate-100 block">${escapeHtml(c.name)}</span>
            </div>
          </label>
        `;
      }).join('');

      // Render summary chips
      if (selectedCategories.length === 0) {
        chipsContainer.innerHTML = '<span class="text-red-400 font-bold italic text-[11px]"><i class="fa-solid fa-triangle-exclamation mr-1"></i>None selected (Feed empty)</span>';
      } else if (selectedCategories.length === CANONICAL_CATEGORIES.length) {
        chipsContainer.innerHTML = '<span class="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 font-bold text-[10px]">ALL 7 TARGET CATEGORIES</span>';
      } else {
        chipsContainer.innerHTML = selectedCategories.map(catId => {
          const cat = CANONICAL_CATEGORIES.find(c => c.id === catId);
          const label = cat ? cat.name : catId;
          return `
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700 text-[10px] font-semibold">
              <span class="max-w-[150px] truncate">${escapeHtml(label)}</span>
              <button onclick="toggleCategory('${catId}')" class="text-slate-400 hover:text-white ml-0.5" title="Remove">&times;</button>
            </span>
          `;
        }).join('');
      }
    }

    function toggleCategory(catId) {
      if (selectedCategories.includes(catId)) {
        selectedCategories = selectedCategories.filter(id => id !== catId);
      } else {
        selectedCategories.push(catId);
      }
      try {
        localStorage.setItem('gem_selected_categories', JSON.stringify(selectedCategories));
      } catch (e) {}
      renderCategoryCheckboxes();
      loadDashboardData();
    }

    function selectAllCategories() {
      selectedCategories = CANONICAL_CATEGORIES.map(c => c.id);
      try {
        localStorage.setItem('gem_selected_categories', JSON.stringify(selectedCategories));
      } catch (e) {}
      renderCategoryCheckboxes();
      loadDashboardData();
    }

    function clearAllCategories() {
      selectedCategories = [];
      try {
        localStorage.setItem('gem_selected_categories', JSON.stringify(selectedCategories));
      } catch (e) {}
      renderCategoryCheckboxes();
      loadDashboardData();
    }

    // --- DATA LOADING & BACKEND SYNC ---
    async function loadDashboardData() {
      try {
        // Build URL with scope, status, sorting, and categories
        let url = `/bids/?scope=${encodeURIComponent(currentScope)}&status=${encodeURIComponent(currentFeedStatus)}&sort_by=${encodeURIComponent(currentSortBy)}&location_type=${encodeURIComponent(currentLocationType)}&limit=250`;
        if (selectedCategories && selectedCategories.length > 0) {
          const catParams = selectedCategories.map(c => `categories=${encodeURIComponent(c)}`).join('&');
          url += `&${catParams}`;
        }

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
          document.getElementById('statActiveBids').textContent = `${s.bengaluru_urban_verified != null ? s.bengaluru_urban_verified : s.active_bids} Verified`;
          document.getElementById('statTotalBids').textContent = `${s.total_bids} Total Ingested`;
          if (document.getElementById('statReviewCount')) {
            document.getElementById('statReviewCount').textContent = `${s.review_count || 0} Review`;
          }
          document.getElementById('statExpiredBids').textContent = `${s.expired_bids} Expired Excluded`;
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
    function renderBidsTable() {
      const tbody = document.getElementById('bidsTableBody');
      const q = searchQuery.toLowerCase().trim();

      // If user cleared all categories, feed is empty by definition
      if (!selectedCategories || selectedCategories.length === 0) {
        document.getElementById('lblShownCount').textContent = 0;
        document.getElementById('lblFilteredCount').textContent = 0;
        tbody.innerHTML = `
          <tr>
            <td colspan="7" class="py-14 text-center text-slate-400">
              <i class="fa-solid fa-layer-group text-3xl mb-2 text-slate-600 block"></i>
              <p class="font-bold text-slate-300">No Product Categories Selected</p>
              <p class="text-xs text-slate-500 mt-1">Please select one or more categories above or click <strong>'Select All'</strong> to display tenders.</p>
              <button onclick="selectAllCategories()" class="mt-3 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition">
                Select All 7 Categories
              </button>
            </td>
          </tr>
        `;
        return;
      }

      let filtered = allBids;

      if (q) {
        filtered = filtered.filter(b =>
          (b.bid_number && b.bid_number.toLowerCase().includes(q)) ||
          (b.category_name && b.category_name.toLowerCase().includes(q)) ||
          (b.dept_name && b.dept_name.toLowerCase().includes(q)) ||
          (b.display_location && b.display_location.toLowerCase().includes(q)) ||
          (b.consignee_city && b.consignee_city.toLowerCase().includes(q)) ||
          (b.consignee_state && b.consignee_state.toLowerCase().includes(q)) ||
          (b.pdf_delivery_city && b.pdf_delivery_city.toLowerCase().includes(q)) ||
          (b.pdf_delivery_pincode && b.pdf_delivery_pincode.toLowerCase().includes(q))
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
              <p class="text-xs text-slate-500 mt-1">Try switching tabs or adjusting search query.</p>
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

        // Delivery Location Representation (FEATURE 2)
        let locBadge = '';
        if (b.target_location_status === 'VERIFIED_BENGALURU_URBAN') {
          locBadge = '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-extrabold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 w-max mb-1"><i class="fa-solid fa-circle-check text-[9px]"></i> BENGALURU URBAN VERIFIED</span>';
        } else if (b.target_location_status === 'PARTIALLY_VERIFIED' || b.target_location_status === 'AMBIGUOUS') {
          locBadge = '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/30 w-max mb-1"><i class="fa-solid fa-triangle-exclamation text-[9px]"></i> REVIEW NEEDED</span>';
        } else if (b.target_location_status === 'OUTSIDE_TARGET') {
          locBadge = '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700 w-max mb-1"><i class="fa-solid fa-location-dot text-[9px]"></i> OUTSIDE TARGET</span>';
        }

        let locationMarkup = '';
        if (b.pdf_delivery_city) {
          const pinStr = b.pdf_delivery_pincode ? ` - ${escapeHtml(b.pdf_delivery_pincode)}` : '';
          locationMarkup = `
            <div class="inline-flex flex-col">
              ${locBadge}
              <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-emerald-950/40 text-emerald-300 border border-emerald-500/30 text-[11px] font-bold">
                <i class="fa-solid fa-file-circle-check text-emerald-400 text-xs"></i>
                <span>${escapeHtml(b.pdf_delivery_city)}, ${escapeHtml(b.pdf_delivery_state || '')}</span>
              </span>
              <span class="text-[10px] text-slate-400 mt-0.5 font-mono">PIN: ${escapeHtml(b.pdf_delivery_pincode || 'N/A')} (p.${b.pdf_page_number || '?'})</span>
            </div>
          `;
        } else {
          locationMarkup = `
            <div class="inline-flex flex-col">
              ${locBadge}
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 text-slate-300 border border-slate-800 text-[11px]">
                <i class="fa-solid fa-location-dot ${isExp ? 'text-slate-500' : 'text-emerald-400'}"></i>
                <span>${loc}</span>
              </span>
            </div>
          `;
        }

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
              ${locationMarkup}
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

            <!-- Actions: Details Modal + PDF -->
            <td class="py-3 px-4 whitespace-nowrap align-top text-center">
              <div class="flex items-center justify-center gap-1.5">
                <button onclick="openBidDetailsModal(${b.id})" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-600/20 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/30 transition text-[11px] font-bold" title="View Delivery Address & Inspection Details">
                  <i class="fa-solid fa-circle-info"></i>
                  <span>Details</span>
                </button>
                ${b.bid_url ? `
                  <a href="${b.bid_url}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-red-600 text-slate-300 hover:text-white border border-slate-700 hover:border-red-500 transition text-[11px] font-bold" title="Open Official GeM PDF Document">
                    <i class="fa-solid fa-file-pdf"></i>
                    <span>PDF</span>
                  </a>
                ` : ''}
              </div>
            </td>
          </tr>
        `;
      }).join('');
    }

    // --- MODAL & PDF LOCATION INTELLIGENCE (FEATURE 2) ---
    function openBidDetailsModal(bidId) {
      const bid = allBids.find(b => b.id === bidId);
      if (!bid) return;
      currentModalBid = bid;

      document.getElementById('detailBidNumber').textContent = bid.bid_number;
      document.getElementById('detailCategory').textContent = bid.category_name || 'Unspecified';
      document.getElementById('detailBidStatus').textContent = bid.bid_status || 'ACTIVE';
      document.getElementById('detailDept').textContent = bid.dept_name || 'N/A';
      document.getElementById('detailMinistry').textContent = bid.ministry_name || 'N/A';
      document.getElementById('detailQty').textContent = bid.quantity ? `${bid.quantity} Units` : 'N/A';
      document.getElementById('detailPubDate').textContent = `${bid.published_date || 'N/A'} ${bid.published_time || ''}`;
      document.getElementById('detailEndDate').textContent = `${bid.end_date_formatted || 'N/A'} ${bid.end_time_formatted || ''}`;
      document.getElementById('detailTimeRem').textContent = bid.time_remaining || 'N/A';
      document.getElementById('detailPdfLink').href = bid.bid_url || '#';

      renderModalPdfContent(bid);
      document.getElementById('bidDetailModal').classList.remove('hidden');
    }

    function renderModalPdfContent(bid) {
      const badge = document.getElementById('detailPdfStatusBadge');
      const content = document.getElementById('detailPdfContent');

      const status = bid.pdf_verification_status || 'UNKNOWN';
      badge.textContent = status;

      if (status === 'VERIFIED') {
        badge.className = "px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
      } else if (status === 'PARTIALLY_VERIFIED') {
        badge.className = "px-2.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30";
      } else {
        badge.className = "px-2.5 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700";
      }

      if (bid.pdf_delivery_address && status !== 'UNKNOWN' && status !== 'PDF_UNAVAILABLE') {
        content.innerHTML = `
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pb-2 border-b border-slate-800/60">
            <div>
              <span class="text-[10px] uppercase font-bold text-slate-500 block">Consignee / Reporting Officer</span>
              <p class="font-bold text-slate-100 mt-0.5">${escapeHtml(bid.pdf_delivery_consignee || 'Consignee details in address block')}</p>
            </div>
            <div>
              <span class="text-[10px] uppercase font-bold text-slate-500 block">Organization / Institution</span>
              <p class="font-bold text-slate-100 mt-0.5">${escapeHtml(bid.pdf_delivery_org || bid.dept_name || 'N/A')}</p>
            </div>
          </div>
          <div>
            <span class="text-[10px] uppercase font-bold text-slate-500 block">Full Extracted Delivery Address</span>
            <p class="font-mono text-slate-200 bg-slate-900 p-2.5 rounded-lg border border-slate-800 mt-1 select-all">${escapeHtml(bid.pdf_delivery_address)}</p>
          </div>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-[11px]">
            <div>
              <span class="text-[10px] uppercase font-bold text-slate-500 font-sans block">City / Town</span>
              <span class="font-bold text-slate-200">${escapeHtml(bid.pdf_delivery_city || 'N/A')}</span>
            </div>
            <div>
              <span class="text-[10px] uppercase font-bold text-slate-500 font-sans block">State</span>
              <span class="font-bold text-slate-200">${escapeHtml(bid.pdf_delivery_state || 'N/A')}</span>
            </div>
            <div>
              <span class="text-[10px] uppercase font-bold text-slate-500 font-sans block">PIN Code</span>
              <span class="font-bold text-amber-300">${escapeHtml(bid.pdf_delivery_pincode || 'N/A')}</span>
            </div>
            <div>
              <span class="text-[10px] uppercase font-bold text-slate-500 font-sans block">PDF Page</span>
              <span class="font-bold text-blue-400">Page ${escapeHtml(bid.pdf_page_number || 'Final')}</span>
            </div>
          </div>
        `;
      } else {
        content.innerHTML = `
          <div class="py-4 text-center text-slate-400 space-y-1">
            <i class="fa-solid fa-file-circle-question text-2xl text-slate-600 block mb-1"></i>
            <p class="font-bold text-slate-300">Delivery address could not be verified from the available document.</p>
            <p class="text-[11px] text-slate-500">The PDF document has not yet been processed, or consignee details reside in an unindexed annexure.</p>
          </div>
        `;
      }
    }

    async function runOnDemandPdfExtraction() {
      if (!currentModalBid) return;
      const btn = document.getElementById('btnTriggerPdfExtract');
      const spinner = document.getElementById('extractSpinner');
      spinner.classList.add('fa-spin');
      btn.disabled = true;

      try {
        const res = await fetch(`/bids/${currentModalBid.id}/extract-pdf`, { method: 'POST' });
        if (res.ok) {
          const updatedBid = await res.json();
          currentModalBid = updatedBid;
          // Update in allBids array
          const idx = allBids.findIndex(b => b.id === updatedBid.id);
          if (idx !== -1) allBids[idx] = updatedBid;
          renderModalPdfContent(updatedBid);
          renderBidsTable();
        } else {
          alert('Extraction notice: Official PDF could not be fetched from GeM portal at this moment.');
        }
      } catch (e) {
        console.error('PDF extract error:', e);
      } finally {
        spinner.classList.remove('fa-spin');
        btn.disabled = false;
      }
    }

    function closeBidDetailModal() {
      document.getElementById('bidDetailModal').classList.add('hidden');
      currentModalBid = null;
    }

    // --- INTERACTION HANDLERS ---
    function setScopeTab(scope, status) {
      currentScope = scope;
      currentFeedStatus = status;

      const tabs = [
        { id: 'tabVerified', scope: 'bengaluru_urban', status: 'active', activeClass: 'bg-emerald-600 text-white shadow' },
        { id: 'tabReview', scope: 'review', status: 'all', activeClass: 'bg-amber-600 text-white shadow' },
        { id: 'tabClosingSoon', scope: 'bengaluru_urban', status: 'closing_soon', activeClass: 'bg-blue-600 text-white shadow' },
        { id: 'tabExpired', scope: 'bengaluru_urban', status: 'expired', activeClass: 'bg-slate-700 text-white shadow' },
        { id: 'tabAll', scope: 'all', status: 'all', activeClass: 'bg-blue-600 text-white shadow' },
      ];

      tabs.forEach(t => {
        const btn = document.getElementById(t.id);
        if (!btn) return;
        if (t.scope === scope && t.status === status) {
          btn.className = `px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 whitespace-nowrap ${t.activeClass}`;
        } else {
          btn.className = "px-3 py-1.5 rounded-lg font-bold transition text-slate-400 hover:text-white flex items-center gap-1.5 whitespace-nowrap";
        }
      });
      loadDashboardData();
    }

    function setFeedStatus(status) {
      setScopeTab(currentScope, status);
    }

    function onSortChange() {
      currentSortBy = document.getElementById('sortBySelect').value;
      loadDashboardData();
    }

    function onLocationTypeChange() {
      currentLocationType = document.getElementById('locationTypeSelect').value;
      loadDashboardData();
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

    // Initial Startup Load
    document.addEventListener('DOMContentLoaded', () => {
      renderCategoryCheckboxes();
      loadDashboardData();
    });
  </script>

</body>
</html>
"""

@router.get("/dashboard", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def get_dashboard():
    return DASHBOARD_HTML
