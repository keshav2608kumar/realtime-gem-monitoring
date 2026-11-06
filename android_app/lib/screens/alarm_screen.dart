import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/alarm_service.dart';

class AlarmScreen extends StatefulWidget {
  final String bidNumber;
  final String category;
  final String city;
  final String bidUrl;
  final String keywords;
  final String? endDate;

  const AlarmScreen({
    super.key,
    required this.bidNumber,
    required this.category,
    required this.city,
    required this.bidUrl,
    required this.keywords,
    this.endDate,
  });

  @override
  State<AlarmScreen> createState() => _AlarmScreenState();
}

class _AlarmScreenState extends State<AlarmScreen> with SingleTickerProviderStateMixin {
  late AnimationController _animController;
  late Animation<double> _scaleAnimation;
  bool _isSilenced = false;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    )..repeat(reverse: true);
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.25).animate(_animController);
  }

  @override
  void dispose() {
    _animController.dispose();
    AlarmService.silenceAlarm();
    super.dispose();
  }

  void _silence() {
    AlarmService.silenceAlarm();
    setState(() {
      _isSilenced = true;
    });
    _animController.stop();
  }

  Future<void> _openBidDocument() async {
    _silence();
    if (widget.bidUrl.isNotEmpty) {
      final uri = Uri.parse(widget.bidUrl);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: true,
      onPopInvokedWithResult: (didPop, result) {
        AlarmService.silenceAlarm();
      },
      child: Scaffold(
        backgroundColor: const Color(0xFF1A0505),
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
            child: Column(
              children: [
                // Top flashing beacon
                AnimatedBuilder(
                  animation: _scaleAnimation,
                  builder: (context, child) {
                    return Transform.scale(
                      scale: _isSilenced ? 1.0 : _scaleAnimation.value,
                      child: Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: _isSilenced
                              ? Colors.grey.withOpacity(0.3)
                              : Colors.red.withOpacity(0.35),
                          border: Border.all(
                            color: _isSilenced ? Colors.grey : Colors.redAccent,
                            width: 3,
                          ),
                        ),
                        child: Icon(
                          _isSilenced ? Icons.alarm_off : Icons.alarm_on,
                          size: 64,
                          color: _isSilenced ? Colors.grey : Colors.redAccent,
                        ),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 16),
                Text(
                  _isSilenced ? 'ALARM SILENCED' : '🚨 MATCHING GeM BID ALERT!',
                  style: TextStyle(
                    color: _isSilenced ? Colors.grey : Colors.redAccent,
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Location: ${widget.city}',
                  style: const TextStyle(color: Colors.white70, fontSize: 16),
                ),
                const SizedBox(height: 24),

                // Main Bid Card
                Expanded(
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: const Color(0xFF2D0E0E),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.red.withOpacity(0.5)),
                    ),
                    child: SingleChildScrollView(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildLabel('BID NUMBER'),
                          SelectableText(
                            widget.bidNumber,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const Divider(color: Colors.white24, height: 24),

                          _buildLabel('MATCHED KEYWORDS'),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                            decoration: BoxDecoration(
                              color: Colors.amber.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: Colors.amberAccent),
                            ),
                            child: Text(
                              widget.keywords,
                              style: const TextStyle(
                                color: Colors.amberAccent,
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),

                          _buildLabel('ITEM / SERVICE CATEGORY'),
                          Text(
                            widget.category,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              height: 1.4,
                            ),
                          ),
                          const SizedBox(height: 16),

                          _buildLabel('LOCATION / DELIVERY CITY'),
                          Row(
                            children: [
                              const Icon(Icons.location_on, color: Colors.redAccent, size: 18),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  widget.city,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),

                          _buildLabel('BID END DATE / DEADLINE'),
                          Row(
                            children: [
                              const Icon(Icons.access_time_filled, color: Colors.amberAccent, size: 18),
                              const SizedBox(width: 6),
                              Text(
                                widget.endDate ?? '20 Nov 2026, 05:00 PM',
                                style: const TextStyle(
                                  color: Colors.amberAccent,
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),

                          _buildLabel('OFFICIAL SOURCE'),
                          const Text(
                            'Government e-Marketplace (GeM)',
                            style: TextStyle(color: Colors.white70, fontSize: 14),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Action Buttons
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white12,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        onPressed: _silence,
                        icon: const Icon(Icons.volume_off),
                        label: Text(_isSilenced ? 'Silenced' : 'Silence'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.redAccent,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        onPressed: _openBidDocument,
                        icon: const Icon(Icons.open_in_browser),
                        label: const Text('Open Bid PDF'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                TextButton(
                  onPressed: () {
                    _silence();
                    Navigator.of(context).pop();
                  },
                  child: const Text('Dismiss to Dashboard', style: TextStyle(color: Colors.white54)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Text(
        text,
        style: const TextStyle(
          color: Colors.white38,
          fontSize: 11,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.1,
        ),
      ),
    );
  }
}
