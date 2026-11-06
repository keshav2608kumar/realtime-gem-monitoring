class BidModel {
  final int id;
  final int gemBidId;
  final String bidNumber;
  final String? bidNumberParent;
  final String categoryName;
  final int? quantity;
  final int? bidType;
  final String? ministryName;
  final String? deptName;
  final DateTime? startDate;
  final DateTime? endDate;
  final String consigneeState;
  final String consigneeCity;
  final String bidUrl;
  final DateTime firstSeenAt;

  BidModel({
    required this.id,
    required this.gemBidId,
    required this.bidNumber,
    this.bidNumberParent,
    required this.categoryName,
    this.quantity,
    this.bidType,
    this.ministryName,
    this.deptName,
    this.startDate,
    this.endDate,
    required this.consigneeState,
    required this.consigneeCity,
    required this.bidUrl,
    required this.firstSeenAt,
  });

  factory BidModel.fromJson(Map<String, dynamic> json) {
    return BidModel(
      id: json['id'] ?? 0,
      gemBidId: json['gem_bid_id'] ?? 0,
      bidNumber: json['bid_number'] ?? '',
      bidNumberParent: json['bid_number_parent'],
      categoryName: json['category_name'] ?? 'N/A',
      quantity: json['quantity'],
      bidType: json['bid_type'],
      ministryName: json['ministry_name'],
      deptName: json['dept_name'],
      startDate: json['start_date'] != null ? DateTime.tryParse(json['start_date']) : null,
      endDate: json['end_date'] != null ? DateTime.tryParse(json['end_date']) : null,
      consigneeState: json['consignee_state'] ?? '',
      consigneeCity: json['consignee_city'] ?? '',
      bidUrl: json['bid_url'] ?? '',
      firstSeenAt: json['first_seen_at'] != null
          ? DateTime.tryParse(json['first_seen_at']) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class AlertModel {
  final int id;
  final int profileId;
  final int bidId;
  final String matchedKeywords;
  final bool notificationSent;
  final DateTime? notificationSentAt;
  final DateTime createdAt;
  final BidModel? bid;

  AlertModel({
    required this.id,
    required this.profileId,
    required this.bidId,
    required this.matchedKeywords,
    required this.notificationSent,
    this.notificationSentAt,
    required this.createdAt,
    this.bid,
  });

  factory AlertModel.fromJson(Map<String, dynamic> json) {
    return AlertModel(
      id: json['id'] ?? 0,
      profileId: json['profile_id'] ?? 0,
      bidId: json['bid_id'] ?? 0,
      matchedKeywords: json['matched_keywords'] ?? '',
      notificationSent: json['notification_sent'] ?? false,
      notificationSentAt: json['notification_sent_at'] != null
          ? DateTime.tryParse(json['notification_sent_at'])
          : null,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at']) ?? DateTime.now()
          : DateTime.now(),
      bid: json['bid'] != null ? BidModel.fromJson(json['bid']) : null,
    );
  }
}

class ProfileModel {
  final int id;
  final String name;
  final bool isActive;
  final String state;
  final List<String> cities;
  final List<String> keywords;
  final int pollIntervalSeconds;

  ProfileModel({
    required this.id,
    required this.name,
    required this.isActive,
    required this.state,
    required this.cities,
    required this.keywords,
    required this.pollIntervalSeconds,
  });

  factory ProfileModel.fromJson(Map<String, dynamic> json) {
    return ProfileModel(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      isActive: json['is_active'] ?? true,
      state: json['state'] ?? '',
      cities: List<String>.from(json['cities'] ?? []),
      keywords: List<String>.from(json['keywords'] ?? []),
      pollIntervalSeconds: json['poll_interval_seconds'] ?? 300,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'is_active': isActive,
      'state': state,
      'cities': cities,
      'keywords': keywords,
      'poll_interval_seconds': pollIntervalSeconds,
    };
  }
}

class SystemStatusModel {
  final String status;
  final bool monitorRunning;
  final int totalProfiles;
  final int activeProfiles;
  final int totalBidsInDb;
  final int totalAlerts;
  final DateTime? lastCheck;

  SystemStatusModel({
    required this.status,
    required this.monitorRunning,
    required this.totalProfiles,
    required this.activeProfiles,
    required this.totalBidsInDb,
    required this.totalAlerts,
    this.lastCheck,
  });

  factory SystemStatusModel.fromJson(Map<String, dynamic> json) {
    return SystemStatusModel(
      status: json['status'] ?? 'unknown',
      monitorRunning: json['monitor_running'] ?? false,
      totalProfiles: json['total_profiles'] ?? 0,
      activeProfiles: json['active_profiles'] ?? 0,
      totalBidsInDb: json['total_bids_in_db'] ?? 0,
      totalAlerts: json['total_alerts'] ?? 0,
      lastCheck: json['last_check'] != null ? DateTime.tryParse(json['last_check']) : null,
    );
  }
}
