import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Travel Concierge Client',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: TravelConciergeScreen(),
    );
  }
}

class TravelConciergeScreen extends StatefulWidget {
  @override
  _TravelConciergeScreenState createState() => _TravelConciergeScreenState();
}

class _TravelConciergeScreenState extends State<TravelConciergeScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  List<ChatMessage> _messages = [];
  bool _isLoading = false;
  String _sessionId = '';
  String _userId = '';

  // API Configuration
  static const String BASE_URL = 'http://127.0.0.1:8000';
  static const String APP_NAME = 'travel_concierge';

  @override
  void initState() {
    super.initState();
    _generateSessionInfo();
    _createSession();
  }

  void _generateSessionInfo() {
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    _userId = 'user_$timestamp';
    _sessionId = 'session_$timestamp';
  }

  Future<void> _createSession() async {
    try {
      final url =
          '$BASE_URL/apps/$APP_NAME/users/$_userId/sessions/$_sessionId';
      final response = await http.post(Uri.parse(url));

      if (response.statusCode == 200) {
        print('Session created successfully');
        _addSystemMessage(
          'Connected to Travel Concierge! How can I help you today?',
        );
      } else {
        _addSystemMessage(
          'Failed to create session. Please check if the server is running.',
        );
      }
    } catch (e) {
      _addSystemMessage('Error connecting to server: $e');
    }
  }

  void _addSystemMessage(String text) {
    setState(() {
      _messages.add(
        ChatMessage(
          text: text,
          isUser: false,
          isSystem: true,
          timestamp: DateTime.now(),
        ),
      );
    });
    _scrollToBottom();
  }

  void _addUserMessage(String text) {
    setState(() {
      _messages.add(
        ChatMessage(text: text, isUser: true, timestamp: DateTime.now()),
      );
    });
    _scrollToBottom();
  }

  void _addAgentMessage(String text, String author) {
    setState(() {
      _messages.add(
        ChatMessage(
          text: text,
          isUser: false,
          author: author,
          timestamp: DateTime.now(),
        ),
      );
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage(String promptText) async {
    if (promptText.trim().isEmpty) return;

    _addUserMessage(promptText);
    _messageController.clear();

    setState(() {
      _isLoading = true;
    });

    try {
      await _sendToAgent(promptText);
    } catch (e) {
      _addSystemMessage('Error sending message: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _sendToAgent(String promptText) async {
    final url = '$BASE_URL/run_sse';

    final payload = {
      'session_id': _sessionId,
      'app_name': APP_NAME,
      'user_id': _userId,
      'new_message': {
        'role': 'user',
        'parts': [
          {'text': promptText},
        ],
      },
    };

    final headers = {
      'Content-Type': 'application/json; charset=UTF-8',
      'Accept': 'text/event-stream',
    };

    try {
      final request = http.Request('POST', Uri.parse(url));
      request.headers.addAll(headers);
      request.body = jsonEncode(payload);

      final streamedResponse = await request.send();

      if (streamedResponse.statusCode == 200) {
        await _handleSSEResponse(streamedResponse);
      } else {
        _addSystemMessage('Server error: ${streamedResponse.statusCode}');
      }
    } catch (e) {
      _addSystemMessage('Network error: $e');
    }
  }

  Future<void> _handleSSEResponse(http.StreamedResponse response) async {
    final stream = response.stream.transform(utf8.decoder);

    await for (String chunk in stream) {
      final lines = chunk.split('\n');

      for (String line in lines) {
        line = line.trim();
        if (line.isEmpty || !line.startsWith('data: ')) continue;

        try {
          final jsonString = line.substring(6); // Remove "data: " prefix
          final event = jsonDecode(jsonString);

          _processEvent(event);
        } catch (e) {
          print('Error parsing SSE data: $e');
        }
      }
    }
  }

  void _processEvent(Map<String, dynamic> event) {
    if (!event.containsKey('content')) {
      // Handle error events
      if (event.containsKey('error')) {
        _addSystemMessage('Agent Error: ${event['error']}');
      }
      return;
    }

    final author = event['author'] ?? 'agent';
    final content = event['content'];
    final parts = content['parts'] as List<dynamic>;

    for (var part in parts) {
      // Handle text responses
      if (part.containsKey('text')) {
        final text = part['text'] as String;
        if (text.trim().isNotEmpty) {
          _addAgentMessage(text, author);
        }
      }

      // Handle function calls (for debugging/logging)
      if (part.containsKey('functionCall')) {
        final functionCall = part['functionCall'];
        final functionName = functionCall['name'];
        print('Agent calling function: $functionName');
        // You can show function calls in UI if needed
        // _addSystemMessage('🔧 Agent is calling: $functionName');
      }

      // Handle function responses
      if (part.containsKey('functionResponse')) {
        final functionResponse = part['functionResponse'];
        final functionName = functionResponse['name'];
        print('Function response from: $functionName');

        // Handle specific function responses for rich UI
        _handleFunctionResponse(functionName, functionResponse['response']);
      }
    }
  }

  void _handleFunctionResponse(String functionName, dynamic response) {
    // Here you can handle specific function responses to create rich UI
    switch (functionName) {
      case 'place_agent':
        _addSystemMessage('🏝️ Found destination suggestions');
        break;
      case 'poi_agent':
        _addSystemMessage('📍 Found activities and points of interest');
        break;
      case 'flight_search_agent':
        _addSystemMessage('✈️ Found flight options');
        break;
      case 'hotel_search_agent':
        _addSystemMessage('🏨 Found hotel options');
        break;
      case 'itinerary_agent':
        _addSystemMessage('📅 Generated itinerary');
        break;
      default:
        print('Function response from $functionName: $response');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Travel Concierge'),
        backgroundColor: Colors.blue[600],
        elevation: 0,
      ),
      body: Column(
        children: [
          // Connection Status
          Container(
            width: double.infinity,
            padding: EdgeInsets.symmetric(vertical: 8, horizontal: 16),
            color: Colors.blue[50],
            child: Text(
              'Session: $_sessionId',
              style: TextStyle(fontSize: 12, color: Colors.blue[700]),
            ),
          ),

          // Chat Messages
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                return _buildMessageBubble(_messages[index]);
              },
            ),
          ),

          // Loading Indicator
          if (_isLoading)
            Container(
              padding: EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  SizedBox(width: 12),
                  Text('Agent is thinking...'),
                ],
              ),
            ),

          // Input Area
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: message.isUser
            ? MainAxisAlignment.end
            : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!message.isUser) ...[
            CircleAvatar(
              radius: 16,
              backgroundColor: message.isSystem
                  ? Colors.grey[400]
                  : Colors.blue[400],
              child: Icon(
                message.isSystem ? Icons.info : Icons.smart_toy,
                size: 16,
                color: Colors.white,
              ),
            ),
            SizedBox(width: 8),
          ],

          Flexible(
            child: Container(
              padding: EdgeInsets.symmetric(vertical: 12, horizontal: 16),
              decoration: BoxDecoration(
                color: message.isUser
                    ? Colors.blue[500]
                    : message.isSystem
                    ? Colors.grey[200]
                    : Colors.grey[100],
                borderRadius: BorderRadius.circular(18),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (!message.isUser &&
                      !message.isSystem &&
                      message.author != null)
                    Text(
                      message.author!,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.blue[700],
                      ),
                    ),
                  if (!message.isUser &&
                      !message.isSystem &&
                      message.author != null)
                    SizedBox(height: 4),
                  Text(
                    message.text,
                    style: TextStyle(
                      color: message.isUser ? Colors.white : Colors.black87,
                      fontSize: 16,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    _formatTime(message.timestamp),
                    style: TextStyle(
                      fontSize: 10,
                      color: message.isUser ? Colors.white70 : Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ),
          ),

          if (message.isUser) ...[
            SizedBox(width: 8),
            CircleAvatar(
              radius: 16,
              backgroundColor: Colors.green[400],
              child: Icon(Icons.person, size: 16, color: Colors.white),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            offset: Offset(0, -2),
            blurRadius: 4,
            color: Colors.black.withOpacity(0.1),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _messageController,
              decoration: InputDecoration(
                hintText: 'Ask about travel destinations, planning, booking...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                filled: true,
                fillColor: Colors.grey[100],
                contentPadding: EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 12,
                ),
              ),
              maxLines: null,
              textInputAction: TextInputAction.send,
              onSubmitted: _isLoading ? null : _sendMessage,
            ),
          ),
          SizedBox(width: 12),
          FloatingActionButton(
            onPressed: _isLoading
                ? null
                : () => _sendMessage(_messageController.text),
            child: Icon(Icons.send),
            mini: true,
            backgroundColor: _isLoading ? Colors.grey : Colors.blue[600],
          ),
        ],
      ),
    );
  }

  String _formatTime(DateTime time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}

class ChatMessage {
  final String text;
  final bool isUser;
  final bool isSystem;
  final String? author;
  final DateTime timestamp;

  ChatMessage({
    required this.text,
    required this.isUser,
    this.isSystem = false,
    this.author,
    required this.timestamp,
  });
}
