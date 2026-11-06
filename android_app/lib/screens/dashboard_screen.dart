import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../services/alarm_service.dart';
import 'alarm_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  SystemStatusModel? _status;
  List<BidModel> _allBids = [];
  List<BidModel> _filteredBids = [];
  List<AlertModel> _alerts = [];
  bool _isLoading = true;
  bool _isScanning = false;
  String? _errorMessage;
  String _activeFilter = '';
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final status = await ApiService.getSystemStatus();
    final bids = await ApiService.getBids(limit: 100);
    final alerts = await ApiService.getAlerts(limit: 100);

    if (mounted) {
      setState(() {
        _status = status;
        _allBids = bids;
        _alerts = alerts;
        _isLoading = false;
        if (status == null && bids.isEmpty) {
          _errorMessage = 'Connecting to 24/7 cloud server... Pull down to refresh.';
        }
      });
      _applyFilter();
    }
  }

  void _applyFilter() {
    final query = _searchController.text.toLowerCase().trim();
    setState(() {
      _filteredBids = _allBids.where((b) {
        final cat = b.categoryName.toLowerCase();
        final matchesFilter = _activeFilter.isEmpty || cat.contains(_activeFilter);
        final matchesQuery = query.isEmpty ||
            b.bidNumber.toLowerCase().contains(query) ||
            cat.contains(query) ||
            b.consigneeCity.toLowerCase().contains(query);
        return matchesFilter && matchesQuery;
      }).toList();
    });
  }

  Future<void> _triggerManualPoll() async {
    setState(() => _isScanning = true);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('⚡ Scanning GeM portal live for Bangalore tenders...'),
        backgroundColor: Color(0xFF1E293B),
      ),
    );
    final ok = await ApiService.triggerManualPoll();
    await Future.delayed(const Duration(seconds: 3));
    await _loadData();
    if (mounted) {
      setState(() => _isScanning = false);
    }
  }

  void _testAlarm() {
    AlarmService.triggerAlarm(
      bidNumber: 'GEM/2026/B/8123875',
      category: 'Computer Printer (V2) / Toner Cartridge',
      city: 'Bangalore Urban, KARNATAKA',
      bidUrl: 'https://bidplus.gem.gov.in/showbidDocument/9993172',
      keywords: 'printer, toner',
    );

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => const AlarmScreen(
          bidNumber: 'GEM/2026/B/8123875',
          category: 'Computer Printer (V2) / Toner Cartridge',
          city: 'Bangalore Urban, KARNATAKA',
          bidUrl: 'https://bidplus.gem.gov.in/showbidDocument/9993172',
          keywords: 'printer, toner',
        ),
      ),
    );
  }

  Future<void> _openBidPdf(String url) async {
    if (url.isEmpty) return;
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Cannot open PDF: $url')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF080D19),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0D1322),
        elevation: 0,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.redAccent.withOpacity(0.2),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.redAccent.withOpacity(0.4)),
              ),
              child: const Icon(Icons.cell_tower, color: Colors.redAccent, size: 20),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Text('GeM ', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                    const Text('BidWatch', style: TextStyle(fontWeight: FontWeight.w900, color: Colors.redAccent, fontSize: 16)),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFF10B981).withOpacity(0.15),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFF10B981).withOpacity(0.4)),
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.circle, size: 6, color: Colors.greenAccent),
                          SizedBox(width: 4),
                          Text(
                            'ONLINE',
                            style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.greenAccent),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const Text(
                  'Bangalore 24/7 Tender Monitor',
                  style: TextStyle(fontSize: 10, color: Colors.white54),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: _isScanning
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.cyanAccent))
                : const Icon(Icons.refresh, color: Colors.white70),
            tooltip: 'Refresh / Scan',
            onPressed: _isScanning ? null : _loadData,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.redAccent))
          : RefreshIndicator(
              color: Colors.redAccent,
              backgroundColor: const Color(0xFF0D1322),
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.all(14),
                children: [
                  if (_errorMessage != null) _buildErrorBanner(),

                  // Top 4 Metrics Grid
                  _buildExecutiveMetricsGrid(),
                  const SizedBox(height: 14),

                  // Action Buttons (Alarm Test + Scan Now)
                  _buildActionControls(),
                  const SizedBox(height: 18),

                  // Category Filters
                  _buildCategoryFilterChips(),
                  const SizedBox(height: 12),

                  // Search Bar
                  _buildSearchBox(),
                  const SizedBox(height: 14),

                  // Section Title
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.list_alt, color: Colors.redAccent, size: 18),
                          const SizedBox(width: 6),
                          Text(
                            'LIVE TENDERS FEED (${_filteredBids.length})',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 0.8),
                          ),
                        ],
                      ),
                      Text(
                        _activeFilter.isEmpty ? 'All Categories' : _activeFilter.toUpperCase(),
                        style: const TextStyle(fontSize: 11, color: Colors.white54),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  // Tenders Feed Cards List
                  if (_filteredBids.isEmpty)
                    _buildEmptyState()
                  else
                    ..._filteredBids.map((b) => _buildTenderCard(b)),
                ],
              ),
            ),
    );
  }

  Widget _buildErrorBanner() {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.amber.withOpacity(0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.amber.withOpacity(0.4)),
      ),
      child: Row(
        children: [
          const Icon(Icons.info_outline, color: Colors.amberAccent, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _errorMessage!,
              style: const TextStyle(color: Colors.white70, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExecutiveMetricsGrid() {
    final isOnline = _status != null;
    final totalBids = _status?.totalBidsInDb ?? _allBids.length;
    final alertCount = _status?.totalAlerts ?? _alerts.length;

    return GridView.count(
      crossAxisCount: 2,
      crossAxisSpacing: 10,
      mainAxisSpacing: 10,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      childAspectRatio: 1.7,
      children: [
        // Metric 1: Cloud Engine
        _buildMetricTile(
          title: 'CLOUD ENGINE',
          value: isOnline ? '24/7 Active' : 'Connecting',
          subtitle: 'Scheduled: 300s',
          icon: Icons.shield,
          iconColor: Colors.greenAccent,
          iconBg: Colors.green.withOpacity(0.15),
        ),

        // Metric 2: Target Location
        _buildMetricTile(
          title: 'TARGET REGION',
          value: 'Bangalore Urban',
          subtitle: 'KARNATAKA, India',
          icon: Icons.my_location,
          iconColor: Colors.cyanAccent,
          iconBg: Colors.cyan.withOpacity(0.15),
        ),

        // Metric 3: Target Products
        _buildMetricTile(
          title: 'TARGET PRODUCTS',
          value: 'Toner, Printer',
          subtitle: 'Cartridge & Ink',
          icon: Icons.local_offer,
          iconColor: Colors.amberAccent,
          iconBg: Colors.amber.withOpacity(0.15),
        ),

        // Metric 4: Fired Alerts
        _buildMetricTile(
          title: 'FIRED ALERTS',
          value: '$alertCount Matches',
          subtitle: '$totalBids Tracked in DB',
          icon: Icons.warning_rounded,
          iconColor: Colors.redAccent,
          iconBg: Colors.red.withOpacity(0.2),
          isAlert: alertCount > 0,
        ),
      ],
    );
  }

  Widget _buildMetricTile({
    required String title,
    required String value,
    required String subtitle,
    required IconData icon,
    required Color iconColor,
    required Color iconBg,
    bool isAlert = false,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1322),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isAlert ? Colors.redAccent.withOpacity(0.6) : Colors.white.withOpacity(0.08),
          width: isAlert ? 1.5 : 1,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: iconBg,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: iconColor, size: 22),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  title,
                  style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.white54, letterSpacing: 0.5),
                  maxLines: 1,
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w900,
                    color: isAlert ? Colors.redAccent : Colors.white,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  subtitle,
                  style: const TextStyle(fontSize: 9, color: Colors.white38),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionControls() {
    return Row(
      children: [
        Expanded(
          flex: 6,
          child: ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFDC2626),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              elevation: 4,
            ),
            onPressed: _testAlarm,
            icon: const Icon(Icons.notification_important, color: Colors.white, size: 20),
            label: const Text(
              'Test Alarm Sound',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          flex: 4,
          child: OutlinedButton.icon(
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.white,
              side: BorderSide(color: Colors.white.withOpacity(0.15)),
              backgroundColor: const Color(0xFF0D1322),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            ),
            onPressed: _isScanning ? null : _triggerManualPoll,
            icon: const Icon(Icons.flash_on, color: Colors.cyanAccent, size: 18),
            label: const Text(
              'Scan Now',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCategoryFilterChips() {
    final filters = [
      {'label': 'All', 'kw': ''},
      {'label': 'Printers', 'kw': 'printer'},
      {'label': 'Toners', 'kw': 'toner'},
      {'label': 'Cartridges', 'kw': 'cartridge'},
      {'label': 'Ink', 'kw': 'ink'},
    ];

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: filters.map((f) {
          final isSelected = _activeFilter == f['kw'];
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text(f['label']!),
              selected: isSelected,
              selectedColor: Colors.redAccent,
              backgroundColor: const Color(0xFF0D1322),
              side: BorderSide(
                color: isSelected ? Colors.redAccent : Colors.white.withOpacity(0.08),
              ),
              labelStyle: TextStyle(
                color: isSelected ? Colors.white : Colors.white70,
                fontSize: 12,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              ),
              onSelected: (selected) {
                setState(() {
                  _activeFilter = selected ? f['kw']! : '';
                });
                _applyFilter();
              },
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildSearchBox() {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0D1322),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: TextField(
        controller: _searchController,
        onChanged: (_) => _applyFilter(),
        style: const TextStyle(fontSize: 13, color: Colors.white),
        decoration: InputDecoration(
          hintText: 'Search Tender #, Category, Department...',
          hintStyle: const TextStyle(color: Colors.white38, fontSize: 13),
          prefixIcon: const Icon(Icons.search, color: Colors.white38, size: 20),
          suffixIcon: _searchController.text.isNotEmpty
              ? IconButton(
                  icon: const Icon(Icons.clear, color: Colors.white38, size: 18),
                  onPressed: () {
                    _searchController.clear();
                    _applyFilter();
                  },
                )
              : null,
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        ),
      ),
    );
  }

  Widget _buildTenderCard(BidModel bid) {
    final catLower = bid.categoryName.toLowerCase();
    final isMatched = catLower.contains('printer') ||
        catLower.contains('toner') ||
        catLower.contains('cartridge') ||
        catLower.contains('ink');

    final dateStr = bid.endDate != null
        ? DateFormat('dd MMM yyyy, hh:mm a').format(bid.endDate!.toLocal())
        : 'Active Listing';

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isMatched ? const Color(0xFF1E0A0A) : const Color(0xFF0D1322),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isMatched ? Colors.redAccent.withOpacity(0.5) : Colors.white.withOpacity(0.08),
          width: isMatched ? 1.5 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: Bid Number & Beacon
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  if (isMatched) ...[
                    Container(
                      width: 8,
                      height: 8,
                      decoration: const BoxDecoration(
                        color: Colors.redAccent,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 6),
                  ],
                  SelectableText(
                    bid.bidNumber,
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
              if (isMatched)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.redAccent.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.redAccent),
                  ),
                  child: const Text(
                    'MATCHED TARGET',
                    style: TextStyle(color: Colors.redAccent, fontSize: 9, fontWeight: FontWeight.bold),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 8),

          // Category Name
          Text(
            bid.categoryName,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: Colors.white,
              height: 1.3,
            ),
          ),
          const SizedBox(height: 10),

          // Location & Date Pills
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.location_on, color: Colors.redAccent, size: 12),
                    const SizedBox(width: 4),
                    Text(
                      '${bid.consigneeCity.isEmpty ? "Bangalore" : bid.consigneeCity}, ${bid.consigneeState}',
                      style: const TextStyle(fontSize: 11, color: Colors.white70),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'End: $dateStr',
                  style: const TextStyle(fontSize: 11, color: Colors.white38),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Official PDF Button (Full Width, Prominent Green)
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF064E3B),
                foregroundColor: Colors.greenAccent,
                padding: const EdgeInsets.symmetric(vertical: 11),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(color: Colors.greenAccent.withOpacity(0.4)),
                ),
                elevation: 0,
              ),
              onPressed: () => _openBidPdf(bid.bidUrl),
              icon: const Icon(Icons.picture_as_pdf, color: Colors.greenAccent, size: 18),
              label: const Text(
                'Open Official GeM PDF',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 20),
      alignment: Alignment.center,
      child: Column(
        children: [
          Icon(Icons.inbox, size: 48, color: Colors.white.withOpacity(0.2)),
          const SizedBox(height: 12),
          const Text(
            'No matching tenders found in cache',
            style: TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          const Text(
            'Tap "Scan Now" above to query GeM portal live.',
            style: TextStyle(color: Colors.white38, fontSize: 12),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
