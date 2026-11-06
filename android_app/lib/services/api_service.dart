import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';

class ApiService {
  static const String _keyBaseUrl = 'gem_api_base_url';
  // Default emulator host; can be changed in App Settings to cloud URL or local IP
  static const String _defaultUrl = 'http://10.0.2.2:8000';

  static Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyBaseUrl) ?? _defaultUrl;
  }

  static Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyBaseUrl, url.trim().replaceAll(RegExp(r'/+$'), ''));
  }

  static Future<SystemStatusModel?> getSystemStatus() async {
    try {
      final base = await getBaseUrl();
      final res = await http.get(Uri.parse('$base/health/')).timeout(const Duration(seconds: 8));
      if (res.statusCode == 200) {
        return SystemStatusModel.fromJson(jsonDecode(res.body));
      }
    } catch (_) {}
    return null;
  }

  static Future<List<AlertModel>> getAlerts({int skip = 0, int limit = 50}) async {
    try {
      final base = await getBaseUrl();
      final res = await http.get(Uri.parse('$base/alerts/?skip=$skip&limit=$limit')).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        final List list = jsonDecode(res.body);
        return list.map((e) => AlertModel.fromJson(e)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<List<BidModel>> getBids({int skip = 0, int limit = 20, String? keyword}) async {
    try {
      final base = await getBaseUrl();
      var uri = '$base/bids/?skip=$skip&limit=$limit';
      if (keyword != null && keyword.isNotEmpty) {
        uri += '&keyword=${Uri.encodeComponent(keyword)}';
      }
      final res = await http.get(Uri.parse(uri)).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        final List list = jsonDecode(res.body);
        return list.map((e) => BidModel.fromJson(e)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<List<ProfileModel>> getProfiles() async {
    try {
      final base = await getBaseUrl();
      final res = await http.get(Uri.parse('$base/profiles/')).timeout(const Duration(seconds: 8));
      if (res.statusCode == 200) {
        final List list = jsonDecode(res.body);
        return list.map((e) => ProfileModel.fromJson(e)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<bool> saveProfile(ProfileModel profile) async {
    try {
      final base = await getBaseUrl();
      final res = await http.post(
        Uri.parse('$base/profiles/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(profile.toJson()),
      ).timeout(const Duration(seconds: 8));
      return res.statusCode == 201;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> updateProfile(int id, Map<String, dynamic> changes) async {
    try {
      final base = await getBaseUrl();
      final res = await http.patch(
        Uri.parse('$base/profiles/$id'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(changes),
      ).timeout(const Duration(seconds: 8));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> deleteProfile(int id) async {
    try {
      final base = await getBaseUrl();
      final res = await http.delete(Uri.parse('$base/profiles/$id')).timeout(const Duration(seconds: 8));
      return res.statusCode == 204;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> triggerManualPoll() async {
    try {
      final base = await getBaseUrl();
      final res = await http.post(Uri.parse('$base/health/trigger-poll')).timeout(const Duration(seconds: 8));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> registerDeviceToken(String fcmToken, {String? deviceName}) async {
    try {
      final base = await getBaseUrl();
      final res = await http.post(
        Uri.parse('$base/devices/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'fcm_token': fcmToken,
          'device_name': deviceName ?? 'Android Phone',
        }),
      ).timeout(const Duration(seconds: 8));
      return res.statusCode == 201;
    } catch (_) {
      return false;
    }
  }
}
