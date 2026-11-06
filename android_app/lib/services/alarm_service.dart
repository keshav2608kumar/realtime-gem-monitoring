import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:vibration/vibration.dart';
import 'package:audioplayers/audioplayers.dart';

class AlarmService {
  static final FlutterLocalNotificationsPlugin _notifications = FlutterLocalNotificationsPlugin();
  static final AudioPlayer _audioPlayer = AudioPlayer();
  static bool _isAlarmActive = false;
  static Timer? _vibrationTimer;

  static const String channelId = 'gem_bid_alerts';
  static const String channelName = 'GeM Bid Loud Alerts';
  static const String channelDesc = 'High priority alarm notifications for matching GeM bids';

  static Future<void> initialize({required Function(String? payload) onNotificationSelect}) async {
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidInit);

    await _notifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: (NotificationResponse response) {
        onNotificationSelect(response.payload);
      },
    );

    // Create high importance alarm channel
    final androidChannel = AndroidNotificationChannel(
      channelId,
      channelName,
      description: channelDesc,
      importance: Importance.max,
      playSound: true,
      enableVibration: true,
      vibrationPattern: Int64List.fromList([0, 1000, 500, 1000, 500, 1000]),
    );

    await _notifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(androidChannel);

    // Request permissions for Android 13+
    await _notifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.requestNotificationsPermission();
  }

  /// Triggers full alarm: Loud Sound + Vibration + Max Priority Notification
  static Future<void> triggerAlarm({
    required String bidNumber,
    required String category,
    required String city,
    required String bidUrl,
    required String keywords,
  }) async {
    _isAlarmActive = true;

    // 1. Play looping alarm sound
    try {
      await _audioPlayer.setReleaseMode(ReleaseMode.loop);
      await _audioPlayer.setVolume(1.0);
      // Play bundled alarm audio or system sound
      await _audioPlayer.play(AssetSource('sounds/alarm.mp3'));
    } catch (_) {
      // Fallback if asset is missing: system notification sound handles it
    }

    // 2. Continuous strong vibration pattern
    _startVibrationLoop();

    // 3. Post full-screen alarm notification
    final androidDetails = AndroidNotificationDetails(
      channelId,
      channelName,
      channelDescription: channelDesc,
      importance: Importance.max,
      priority: Priority.max,
      fullScreenIntent: true,
      category: AndroidNotificationCategory.alarm,
      audioAttributesUsage: AudioAttributesUsage.alarm,
      visibility: NotificationVisibility.public,
      ongoing: true, // Cannot be dismissed by swiping
      autoCancel: false,
      color: Colors.red,
      ledColor: Colors.red,
      ledOnMs: 1000,
      ledOffMs: 500,
      enableLights: true,
      enableVibration: true,
      vibrationPattern: Int64List.fromList([0, 1000, 500, 1000, 500, 1000]),
      styleInformation: BigTextStyleInformation(
        'BID: $bidNumber\n\n'
        'Location: $city\n'
        'Matched: $keywords\n\n'
        '$category',
        contentTitle: '🚨 GeM BID ALARM: $city',
        summaryText: 'Action Required',
      ),
    );

    final notificationDetails = NotificationDetails(android: androidDetails);

    final payload = '$bidNumber|$city|$category|$bidUrl|$keywords';

    await _notifications.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      '🚨 GeM BID MATCH: $city',
      '$bidNumber: $category',
      notificationDetails,
      payload: payload,
    );
  }

  static void _startVibrationLoop() {
    _vibrationTimer?.cancel();
    _vibrationTimer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      if (!_isAlarmActive) {
        timer.cancel();
        return;
      }
      final hasVib = await Vibration.hasVibrator();
      if (hasVib == true) {
        Vibration.vibrate(pattern: [0, 800, 300, 800], intensities: [0, 255, 0, 255]);
      }
    });
  }

  /// Silences the alarm and stops vibration
  static Future<void> silenceAlarm() async {
    _isAlarmActive = false;
    _vibrationTimer?.cancel();
    try {
      await _audioPlayer.stop();
      Vibration.cancel();
    } catch (_) {}
  }

  static bool get isAlarmActive => _isAlarmActive;
}
