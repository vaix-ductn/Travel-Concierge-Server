/// API Configuration for Travel Concierge Client
class ApiConfig {
  // Server Configuration
  static const String baseUrl = 'http://127.0.0.1:8000';
  static const String appName = 'travel_concierge';

  // Endpoints
  static const String sessionEndpoint = '/apps/$appName/users';
  static const String messageEndpoint = '/run_sse';
  static const String docsEndpoint = '/docs';

  // HTTP Headers
  static const Map<String, String> jsonHeaders = {
    'Content-Type': 'application/json; charset=UTF-8',
  };

  static const Map<String, String> sseHeaders = {
    'Content-Type': 'application/json; charset=UTF-8',
    'Accept': 'text/event-stream',
  };

  // Timeouts
  static const Duration connectionTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 60);

  // Build full session URL
  static String getSessionUrl(String userId, String sessionId) {
    return '$baseUrl$sessionEndpoint/$userId/sessions/$sessionId';
  }

  // Build message URL
  static String getMessageUrl() {
    return '$baseUrl$messageEndpoint';
  }

  // Build API docs URL
  static String getDocsUrl() {
    return '$baseUrl$docsEndpoint';
  }
}

/// Message payload structure
class MessagePayload {
  final String sessionId;
  final String appName;
  final String userId;
  final UserMessage newMessage;

  MessagePayload({
    required this.sessionId,
    required this.appName,
    required this.userId,
    required this.newMessage,
  });

  Map<String, dynamic> toJson() {
    return {
      'session_id': sessionId,
      'app_name': appName,
      'user_id': userId,
      'new_message': newMessage.toJson(),
    };
  }
}

/// User message structure
class UserMessage {
  final String role;
  final List<MessagePart> parts;

  UserMessage({
    this.role = 'user',
    required this.parts,
  });

  UserMessage.text(String text)
      : role = 'user',
        parts = [MessagePart.text(text)];

  Map<String, dynamic> toJson() {
    return {
      'role': role,
      'parts': parts.map((part) => part.toJson()).toList(),
    };
  }
}

/// Message part structure
class MessagePart {
  final String? text;
  final Map<String, dynamic>? functionCall;
  final Map<String, dynamic>? functionResponse;

  MessagePart({this.text, this.functionCall, this.functionResponse});

  MessagePart.text(String text)
      : text = text,
        functionCall = null,
        functionResponse = null;

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> json = {};
    if (text != null) json['text'] = text;
    if (functionCall != null) json['functionCall'] = functionCall;
    if (functionResponse != null) json['functionResponse'] = functionResponse;
    return json;
  }
}

/// API Response Event structure
class ApiEvent {
  final String? author;
  final EventContent? content;
  final String? error;

  ApiEvent({this.author, this.content, this.error});

  factory ApiEvent.fromJson(Map<String, dynamic> json) {
    return ApiEvent(
      author: json['author'],
      content: json['content'] != null
          ? EventContent.fromJson(json['content'])
          : null,
      error: json['error'],
    );
  }

  bool get hasError => error != null;
  bool get hasContent => content != null;
}

/// Event content structure
class EventContent {
  final List<MessagePart> parts;

  EventContent({required this.parts});

  factory EventContent.fromJson(Map<String, dynamic> json) {
    final List<dynamic> partsJson = json['parts'] ?? [];
    final List<MessagePart> parts = partsJson.map((partJson) {
      return MessagePart(
        text: partJson['text'],
        functionCall: partJson['functionCall'],
        functionResponse: partJson['functionResponse'],
      );
    }).toList();

    return EventContent(parts: parts);
  }

  /// Get all text parts from content
  List<String> getTextParts() {
    return parts
        .where((part) => part.text != null && part.text!.trim().isNotEmpty)
        .map((part) => part.text!)
        .toList();
  }

  /// Get all function calls
  List<Map<String, dynamic>> getFunctionCalls() {
    return parts
        .where((part) => part.functionCall != null)
        .map((part) => part.functionCall!)
        .toList();
  }

  /// Get all function responses
  List<Map<String, dynamic>> getFunctionResponses() {
    return parts
        .where((part) => part.functionResponse != null)
        .map((part) => part.functionResponse!)
        .toList();
  }
}
