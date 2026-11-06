import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';
import '../services/alarm_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _urlController = TextEditingController();
  bool _isTesting = false;
  String? _testResult;

  @override
  void initState() {
    super.initState();
    _loadUrl();
  }

  Future<void> _loadUrl() async {
    final url = await ApiService.getBaseUrl();
    _urlController.text = url;
  }

  Future<void> _saveAndTest() async {
    setState(() {
      _isTesting = true;
      _testResult = null;
    });

    await ApiService.setBaseUrl(_urlController.text);
    final status = await ApiService.getSystemStatus();

    setState(() {
      _isTesting = false;
      if (status != null) {
        _testResult = '✅ Connected! 24/7 Monitor: ${status.monitorRunning ? "Active" : "Paused"} (${status.totalBidsInDb} bids in DB)';
      } else {
        _testResult = '❌ Could not connect to backend at ${_urlController.text}';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings & Configuration')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Server URL Card
          Card(
            color: const Color(0xFF1E2230),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Cloud Backend API URL', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  const Text(
                    'Enter your 24/7 cloud server address (e.g. http://192.168.1.x:8000 or https://your-server.com)',
                    style: TextStyle(color: Colors.white54, fontSize: 12),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _urlController,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      hintText: 'http://10.0.2.2:8000',
                      prefixIcon: Icon(Icons.dns),
                    ),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _isTesting ? null : _saveAndTest,
                      icon: _isTesting
                          ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.check_circle_outline),
                      label: const Text('Save & Test Connection'),
                    ),
                  ),
                  if (_testResult != null) ...[
                    const SizedBox(height: 10),
                    Text(
                      _testResult!,
                      style: TextStyle(
                        color: _testResult!.startsWith('✅') ? Colors.greenAccent : Colors.redAccent,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Alarm Sound & Vibration Test
          Card(
            color: const Color(0xFF1E2230),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Alarm Sound & Vibration', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  const Text(
                    'Verify that your phone produces a loud sound and vibration when an alert fires.',
                    style: TextStyle(color: Colors.white54, fontSize: 12),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
                          onPressed: () {
                            AlarmService.triggerAlarm(
                              bidNumber: 'TEST/ALERT/2026',
                              category: 'Sound & Vibration Test',
                              city: 'Bangalore, KARNATAKA',
                              bidUrl: '',
                              keywords: 'printer, toner',
                            );
                          },
                          icon: const Icon(Icons.volume_up, color: Colors.white),
                          label: const Text('Test Alarm Sound', style: TextStyle(color: Colors.white)),
                        ),
                      ),
                      const SizedBox(width: 10),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.grey[800]),
                        onPressed: AlarmService.silenceAlarm,
                        child: const Text('Silence'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Critical Android Permissions Note
          Card(
            color: const Color(0xFF261D15),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(color: Colors.amberAccent.withOpacity(0.5)),
            ),
            child: const Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.battery_alert, color: Colors.amberAccent),
                      SizedBox(width: 8),
                      Text(
                        'CRITICAL: 24/7 Alert Delivery Guide',
                        style: TextStyle(color: Colors.amberAccent, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  SizedBox(height: 10),
                  Text(
                    'To ensure your phone rings even when locked or app is closed:\n\n'
                    '1. Battery Optimization: Go to Android Settings > Apps > GeM BidWatch > Battery > Choose "Unrestricted".\n\n'
                    '2. Do Not Disturb: Allow GeM BidWatch alerts through DND if needed.\n\n'
                    '3. Auto-Start: On Xiaomi/Oppo/Vivo/Realme, enable "Auto-start" in App Permissions.',
                    style: TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
