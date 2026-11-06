import 'dart:async';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'alarm_service.dart';
import 'api_service.dart';

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // Must initialize Firebase inside background isolate
  try {
    await Firebase.initializeApp();
  } catch (_) {}

  final data = message.data;
  final bidNumber = data['bid_number'] ?? message.notification?.title ?? 'New Bid';
  final category = data['category'] ?? message.notification?.body ?? 'GeM Match';
  final city = data['city'] ?? 'India';
  final bidUrl = data['bid_url'] ?? '';
  final keywords = data['matched_keywords'] ?? 'Filter Matched';

  // Trigger immediate loud alarm and vibration even when app is terminated!
  await AlarmService.triggerAlarm(
    bidNumber: bidNumber,
    category: category,
    city: city,
    bidUrl: bidUrl,
    keywords: keywords,
  );
}

class FcmService {
  static Future<void> initialize({
    required Function(Map<String, dynamic> data) onAlarmTriggered,
  }) async {
    try {
      await Firebase.initializeApp();
    } catch (_) {
      // Firebase might not be configured yet during initial local dev
      return;
    }

    final messaging = FirebaseMessaging.instance;

    // Request permissions
    final settings = await messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
      criticalAlert: true,
      announcement: true,
    );

    // Register background handler
    FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);

    // Foreground listener
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      final data = message.data;
      final bidNumber = data['bid_number'] ?? message.notification?.title ?? 'New Bid';
      final category = data['category'] ?? message.notification?.body ?? 'GeM Match';
      final city = data['city'] ?? 'India';
      final bidUrl = data['bid_url'] ?? '';
      final keywords = data['matched_keywords'] ?? '';

      AlarmService.triggerAlarm(
        bidNumber: bidNumber,
        category: category,
        city: city,
        bidUrl: bidUrl,
        keywords: keywords,
      );

      onAlarmTriggered(data);
    });

    // When notification is tapped
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      onAlarmTriggered(message.data);
    });

    // Get and register token
    try {
      final token = await messaging.getToken();
      if (token != null) {
        await ApiService.registerDeviceToken(token);
      }
      messaging.onTokenRefresh.listen((newToken) {
        ApiService.registerDeviceToken(newToken);
      });
    } catch (_) {}
  }
}
