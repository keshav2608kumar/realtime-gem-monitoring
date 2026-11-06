import 'package:flutter/material.dart';
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
  List<AlertModel> _recentAlerts = [];
  List<ProfileModel> _profiles = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final status = await ApiService.getSystemStatus();
    final alerts = await ApiService.getAlerts(limit: 5);
    final profiles = await ApiService.getProfiles();

    if (mounted) {
      setState(() {
        _status = status;
        _recentAlerts = alerts;
        _profiles = profiles;
        _isLoading = false;
        if (status == null) {
          _errorMessage = 'Cannot connect to backend server. Check settings.';
        }
      });
    }
  }

  Future<void> _triggerManualPoll() async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Triggering immediate GeM scan...')),
    );
    final ok = await ApiService.triggerManualPoll();
    if (ok) {
      await Future.delayed(const Duration(seconds: 4));
      _loadData();
    }
  }

  void _testAlarm() {
    AlarmService.triggerAlarm(
      bidNumber: 'TEST/GEM/2026/001',
      category: 'Computer Printer & Toner Cartridge (Test Alarm)',
      city: 'Bangalore Urban, KARNATAKA',
      bidUrl: 'https://bidplus.gem.gov.in/all-bids',
      keywords: 'printer, toner',
    );

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => const AlarmScreen(
          bidNumber: 'TEST/GEM/2026/001',
          category: 'Computer Printer & Toner Cartridge (Test Alarm)',
          city: 'Bangalore Urban, KARNATAKA',
          bidUrl: 'https://bidplus.gem.gov.in/all-bids',
          keywords: 'printer, toner',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.shield_outlined, color: Colors.blueAccent),
            SizedBox(width: 8),
            Text('GeM BidWatch', style: TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (_errorMessage != null) _buildErrorCard(),
                  _buildStatusCard(),
                  const SizedBox(height: 16),
                  _buildActionButtons(),
                  const SizedBox(height: 20),
                  _buildProfilesSummary(),
                  const SizedBox(height: 20),
                  _buildRecentAlerts(),
                ],
              ),
            ),
    );
  }

  Widget _buildErrorCard() {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.red.withOpacity(0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.redAccent.withOpacity(0.5)),
      ),
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded, color: Colors.redAccent),
          const SizedBox(width: 10),
          Expanded(child: Text(_errorMessage!, style: const TextStyle(color: Colors.white70))),
        ],
      ),
    );
  }

  Widget _buildStatusCard() {
    final isOnline = _status != null;
    final isMonitoring = _status?.monitorRunning ?? false;

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      color: const Color(0xFF1E2230),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: isOnline && isMonitoring ? Colors.greenAccent : Colors.orangeAccent,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      isOnline ? (isMonitoring ? '24/7 CLOUD ACTIVE' : 'MONITOR PAUSED') : 'OFFLINE',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: isOnline && isMonitoring ? Colors.greenAccent : Colors.orangeAccent,
                        fontSize: 13,
                        letterSpacing: 1.1,
                      ),
                    ),
                  ],
                ),
                Text(
                  _status?.lastCheck != null
                      ? DateFormat('hh:mm a').format(_status!.lastCheck!.toLocal())
                      : 'Never',
                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                ),
              ],
            ),
            const Divider(height: 24, color: Colors.white12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatItem('Bids Scanned', '${_status?.totalBidsInDb ?? 0}', Icons.radar),
                _buildStatItem('Alerts Triggered', '${_status?.totalAlerts ?? 0}', Icons.notification_important, color: Colors.redAccent),
                _buildStatItem('Active Profiles', '${_status?.activeProfiles ?? 0}', Icons.tune),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, IconData icon, {Color? color}) {
    return Column(
      children: [
        Icon(icon, size: 22, color: color ?? Colors.blueAccent),
        const SizedBox(height: 6),
        Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color ?? Colors.white)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.white54)),
      ],
    );
  }

  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
          child: ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF2C3246),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 13),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: _triggerManualPoll,
            icon: const Icon(Icons.flash_on, color: Colors.amberAccent, size: 20),
            label: const Text('Scan Now'),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF4A1515),
              foregroundColor: Colors.redAccent,
              padding: const EdgeInsets.symmetric(vertical: 13),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: _testAlarm,
            icon: const Icon(Icons.alarm, color: Colors.redAccent, size: 20),
            label: const Text('Test Alarm'),
          ),
        ),
      ],
    );
  }

  Widget _buildProfilesSummary() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Active Monitoring Profiles', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),
        if (_profiles.isEmpty)
          const Text('No profiles configured yet', style: TextStyle(color: Colors.white54))
        else
          ..._profiles.map((p) => Card(
                color: const Color(0xFF1E2230),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                child: ListTile(
                  leading: const Icon(Icons.location_on, color: Colors.redAccent),
                  title: Text(p.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text(
                    '${p.state} • ${p.cities.join(', ')}\nKeywords: ${p.keywords.join(', ')}',
                    style: const TextStyle(fontSize: 12, color: Colors.white70),
                  ),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: p.isActive ? Colors.green.withOpacity(0.2) : Colors.grey.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      p.isActive ? 'RUNNING' : 'STOPPED',
                      style: TextStyle(
                        color: p.isActive ? Colors.greenAccent : Colors.grey,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              )),
      ],
    );
  }

  Widget _buildRecentAlerts() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Recent Bid Alerts', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),
        if (_recentAlerts.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 20),
            child: Center(
              child: Text('No bid alerts yet. The 24/7 worker is monitoring.', style: TextStyle(color: Colors.white54)),
            ),
          )
        else
          ..._recentAlerts.map((alert) {
            final bid = alert.bid;
            return Card(
              color: const Color(0xFF261818),
              margin: const EdgeInsets.only(bottom: 10),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
                side: BorderSide(color: Colors.redAccent.withOpacity(0.3)),
              ),
              child: ListTile(
                leading: const CircleAvatar(
                  backgroundColor: Colors.redAccent,
                  child: Icon(Icons.warning, color: Colors.white, size: 20),
                ),
                title: Text(
                  bid?.bidNumber ?? 'Bid #${alert.bidId}',
                  style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
                ),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 4),
                    Text(
                      bid?.categoryName ?? 'Category',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 13, color: Colors.white70),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Text('Matched: ${alert.matchedKeywords}', style: const TextStyle(color: Colors.amberAccent, fontSize: 11)),
                        const Spacer(),
                        Text(DateFormat('dd MMM hh:mm a').format(alert.createdAt.toLocal()), style: const TextStyle(color: Colors.white38, fontSize: 11)),
                      ],
                    ),
                  ],
                ),
                onTap: () {
                  if (bid != null) {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => AlarmScreen(
                          bidNumber: bid.bidNumber,
                          category: bid.categoryName,
                          city: '${bid.consigneeCity}, ${bid.consigneeState}',
                          bidUrl: bid.bidUrl,
                          keywords: alert.matchedKeywords,
                        ),
                      ),
                    );
                  }
                },
              ),
            );
          }),
      ],
    );
  }
}
