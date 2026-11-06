import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class ProfilesScreen extends StatefulWidget {
  const ProfilesScreen({super.key});

  @override
  State<ProfilesScreen> createState() => _ProfilesScreenState();
}

class _ProfilesScreenState extends State<ProfilesScreen> {
  List<ProfileModel> _profiles = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProfiles();
  }

  Future<void> _loadProfiles() async {
    setState(() => _isLoading = true);
    final p = await ApiService.getProfiles();
    if (mounted) {
      setState(() {
        _profiles = p;
        _isLoading = false;
      });
    }
  }

  Future<void> _toggleActive(ProfileModel profile) async {
    final ok = await ApiService.updateProfile(profile.id, {'is_active': !profile.isActive});
    if (ok) _loadProfiles();
  }

  void _showAddProfileDialog() {
    final nameCtrl = TextEditingController();
    final stateCtrl = TextEditingController(text: 'KARNATAKA');
    final citiesCtrl = TextEditingController(text: 'BANGALORE, Bangalore Urban, BENGALURU URBAN, Bengaluru');
    final keywordsCtrl = TextEditingController(text: 'toner, cartridge, printer, ink');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E2230),
        title: const Text('Add Monitoring Profile'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                decoration: const InputDecoration(labelText: 'Profile Name', hintText: 'e.g. Bangalore Toner Bids'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: stateCtrl,
                decoration: const InputDecoration(labelText: 'State', hintText: 'e.g. KARNATAKA'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: citiesCtrl,
                decoration: const InputDecoration(
                  labelText: 'Cities (comma-separated)',
                  hintText: 'BANGALORE, Bangalore Urban',
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: keywordsCtrl,
                decoration: const InputDecoration(
                  labelText: 'Keywords (comma-separated)',
                  hintText: 'toner, cartridge, printer',
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              final newP = ProfileModel(
                id: 0,
                name: nameCtrl.text.trim(),
                isActive: true,
                state: stateCtrl.text.trim(),
                cities: citiesCtrl.text.split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList(),
                keywords: keywordsCtrl.text.split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList(),
                pollIntervalSeconds: 300,
              );
              Navigator.pop(ctx);
              await ApiService.saveProfile(newP);
              _loadProfiles();
            },
            child: const Text('Save Profile'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Monitoring Profiles'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadProfiles),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddProfileDialog,
        child: const Icon(Icons.add),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _profiles.isEmpty
              ? const Center(child: Text('No profiles configured.', style: TextStyle(color: Colors.white54)))
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: _profiles.length,
                  itemBuilder: (context, index) {
                    final p = _profiles[index];
                    return Card(
                      color: const Color(0xFF1E2230),
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Text(p.name, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                                const Spacer(),
                                Switch(
                                  value: p.isActive,
                                  onChanged: (_) => _toggleActive(p),
                                  activeColor: Colors.greenAccent,
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            Text('State: ${p.state}', style: const TextStyle(color: Colors.white70)),
                            const SizedBox(height: 4),
                            Text('Cities: ${p.cities.join(', ')}', style: const TextStyle(color: Colors.white70)),
                            const SizedBox(height: 4),
                            Text('Keywords: ${p.keywords.join(', ')}', style: const TextStyle(color: Colors.amberAccent)),
                            const Divider(height: 20, color: Colors.white12),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text('Poll Interval: ${p.pollIntervalSeconds ~/ 60} min', style: const TextStyle(color: Colors.white38, fontSize: 12)),
                                IconButton(
                                  icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 20),
                                  onPressed: () async {
                                    final confirm = await showDialog<bool>(
                                      context: context,
                                      builder: (ctx) => AlertDialog(
                                        title: const Text('Delete Profile?'),
                                        content: Text('Delete "${p.name}"?'),
                                        actions: [
                                          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
                                          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Delete', style: TextStyle(color: Colors.redAccent))),
                                        ],
                                      ),
                                    );
                                    if (confirm == true) {
                                      await ApiService.deleteProfile(p.id);
                                      _loadProfiles();
                                    }
                                  },
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
