import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import 'alarm_screen.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  List<AlertModel> _alerts = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadAlerts();
  }

  Future<void> _loadAlerts() async {
    setState(() => _isLoading = true);
    final alerts = await ApiService.getAlerts(limit: 100);
    if (mounted) {
      setState(() {
        _alerts = alerts;
        _isLoading = false;
      });
    }
  }

  Future<void> _openPdf(String url) async {
    if (url.isNotEmpty) {
      final uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('All Bid Alerts'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadAlerts),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _alerts.isEmpty
              ? const Center(child: Text('No alerts found.', style: TextStyle(color: Colors.white54)))
              : RefreshIndicator(
                  onRefresh: _loadAlerts,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _alerts.length,
                    itemBuilder: (context, index) {
                      final a = _alerts[index];
                      final b = a.bid;
                      return Card(
                        color: const Color(0xFF1E2230),
                        margin: const EdgeInsets.only(bottom: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                    decoration: BoxDecoration(
                                      color: Colors.redAccent.withOpacity(0.2),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: Text(
                                      b?.bidNumber ?? 'GEM/BID/${a.bidId}',
                                      style: const TextStyle(
                                        color: Colors.redAccent,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 13,
                                      ),
                                    ),
                                  ),
                                  const Spacer(),
                                  Text(
                                    DateFormat('dd MMM yyyy, hh:mm a').format(a.createdAt.toLocal()),
                                    style: const TextStyle(color: Colors.white38, fontSize: 11),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                b?.categoryName ?? 'Category Details',
                                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.white),
                              ),
                              const SizedBox(height: 6),
                              Row(
                                children: [
                                  const Icon(Icons.location_on_outlined, size: 14, color: Colors.white54),
                                  const SizedBox(width: 4),
                                  Text(
                                    '${b?.consigneeCity ?? 'Bangalore'}, ${b?.consigneeState ?? 'KARNATAKA'}',
                                    style: const TextStyle(color: Colors.white70, fontSize: 12),
                                  ),
                                  const SizedBox(width: 12),
                                  const Icon(Icons.local_offer_outlined, size: 14, color: Colors.amberAccent),
                                  const SizedBox(width: 4),
                                  Text(
                                    'Keywords: ${a.matchedKeywords}',
                                    style: const TextStyle(color: Colors.amberAccent, fontSize: 12),
                                  ),
                                ],
                              ),
                              const Divider(height: 18, color: Colors.white12),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.end,
                                children: [
                                  TextButton.icon(
                                    onPressed: () {
                                      if (b != null) {
                                        Navigator.of(context).push(
                                          MaterialPageRoute(
                                            builder: (_) => AlarmScreen(
                                              bidNumber: b.bidNumber,
                                              category: b.categoryName,
                                              city: '${b.consigneeCity}, ${b.consigneeState}',
                                              bidUrl: b.bidUrl,
                                              keywords: a.matchedKeywords,
                                              endDate: b.endDate != null ? DateFormat('dd MMM yyyy, hh:mm a').format(b.endDate!.toLocal()) : '20 Nov 2026, 05:00 PM',
                                            ),
                                          ),
                                        );
                                      }
                                    },
                                    icon: const Icon(Icons.fullscreen, size: 18),
                                    label: const Text('View Alert Screen'),
                                  ),
                                  const SizedBox(width: 8),
                                  ElevatedButton.icon(
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: Colors.blueAccent,
                                      foregroundColor: Colors.white,
                                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                    ),
                                    onPressed: () => _openPdf(b?.bidUrl ?? ''),
                                    icon: const Icon(Icons.picture_as_pdf, size: 16),
                                    label: const Text('Open PDF'),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
