#!/usr/bin/env python3
"""
Simple API client để test Travel Concierge API
Chạy: python test_api_client.py
"""

import json
import requests
import time

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
APP_NAME = "travel_concierge"
USER_ID = f"test_user_{int(time.time())}"
SESSION_ID = f"test_session_{int(time.time())}"

def create_session():
    """Tạo session mới"""
    print(f"🔄 Creating session: {SESSION_ID}")

    url = f"{BASE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"

    try:
        response = requests.post(url)
        if response.status_code == 200:
            print("✅ Session created successfully")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Failed to create session: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return False

def send_message(prompt_text):
    """Gửi message đến agent và nhận response"""
    print(f"\n📤 Sending message: '{prompt_text}'")

    url = f"{BASE_URL}/run_sse"

    payload = {
        "session_id": SESSION_ID,
        "app_name": APP_NAME,
        "user_id": USER_ID,
        "new_message": {
            "role": "user",
            "parts": [
                {"text": prompt_text}
            ]
        }
    }

    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "text/event-stream",
    }

    try:
        with requests.post(url, json=payload, headers=headers, stream=True) as response:
            if response.status_code != 200:
                print(f"❌ Server error: {response.status_code}")
                return False

            print("📨 Receiving response...")

            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        try:
                            json_data = line_text[6:]  # Remove 'data: ' prefix
                            event = json.loads(json_data)
                            process_event(event)
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON parse error: {e}")
                            print(f"Raw data: {line_text}")

            return True

    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def process_event(event):
    """Xử lý event từ SSE stream"""

    # Handle error events
    if "error" in event:
        print(f"🚨 Agent Error: {event['error']}")
        return

    if "content" not in event:
        print(f"⚠️ Unknown event: {event}")
        return

    author = event.get("author", "agent")
    content = event["content"]
    parts = content.get("parts", [])

    for part in parts:
        # Text responses
        if "text" in part:
            text = part["text"].strip()
            if text:
                print(f"🤖 {author}: {text}")

        # Function calls
        if "functionCall" in part:
            function_call = part["functionCall"]
            function_name = function_call["name"]
            args = function_call.get("args", {})
            print(f"🔧 {author} calling: {function_name}")
            print(f"   Args: {json.dumps(args, indent=2)}")

        # Function responses
        if "functionResponse" in part:
            function_response = part["functionResponse"]
            function_name = function_response["name"]
            response_data = function_response.get("response", {})

            print(f"📋 Response from {function_name}:")

            # Handle specific function responses
            if function_name == "place_agent":
                handle_place_response(response_data)
            elif function_name == "poi_agent":
                handle_poi_response(response_data)
            elif function_name == "flight_search_agent":
                handle_flight_response(response_data)
            elif function_name == "hotel_search_agent":
                handle_hotel_response(response_data)
            else:
                print(f"   {json.dumps(response_data, indent=2)}")

def handle_place_response(response):
    """Handle place agent response với format đẹp"""
    if "places" in response:
        places = response["places"]
        print(f"   🏝️ Found {len(places)} destinations:")
        for i, place in enumerate(places, 1):
            name = place.get("name", "Unknown")
            country = place.get("country", "")
            rating = place.get("rating", "N/A")
            highlights = place.get("highlights", "")

            print(f"     {i}. {name}, {country} (⭐ {rating})")
            if highlights:
                print(f"        💡 {highlights}")

def handle_poi_response(response):
    """Handle POI agent response"""
    if "activities" in response:
        activities = response["activities"]
        print(f"   📍 Found {len(activities)} activities:")
        for i, activity in enumerate(activities, 1):
            name = activity.get("name", "Unknown")
            description = activity.get("description", "")
            print(f"     {i}. {name}")
            if description:
                print(f"        🎯 {description}")

def handle_flight_response(response):
    """Handle flight search response"""
    if "flights" in response:
        flights = response["flights"]
        print(f"   ✈️ Found {len(flights)} flights:")
        for i, flight in enumerate(flights, 1):
            airline = flight.get("airline", "Unknown")
            price = flight.get("price", "N/A")
            departure = flight.get("departure_time", "")
            arrival = flight.get("arrival_time", "")

            print(f"     {i}. {airline} - ${price}")
            print(f"        🕒 {departure} → {arrival}")

def handle_hotel_response(response):
    """Handle hotel search response"""
    if "hotels" in response:
        hotels = response["hotels"]
        print(f"   🏨 Found {len(hotels)} hotels:")
        for i, hotel in enumerate(hotels, 1):
            name = hotel.get("name", "Unknown")
            price = hotel.get("price_per_night", "N/A")
            rating = hotel.get("rating", "N/A")

            print(f"     {i}. {name} (⭐ {rating})")
            print(f"        💰 ${price}/night")

def main():
    """Main function để test API"""
    print("🚀 Travel Concierge API Test Client")
    print("=" * 50)

    # Test 1: Create session
    if not create_session():
        print("❌ Cannot create session. Make sure server is running!")
        return

    # Test messages
    test_messages = [
        "Inspire me about destinations in Southeast Asia",
        "Show me activities in Bali",
        "Find flights from Ho Chi Minh City to Bangkok"
    ]

    for message in test_messages:
        print("\n" + "=" * 50)
        success = send_message(message)
        if not success:
            print("❌ Failed to send message")
            break

        print("\n⏳ Waiting 2 seconds before next message...")
        time.sleep(2)

    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    main()