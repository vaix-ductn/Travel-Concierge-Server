# Google Maps Integration for Inspiration Agent

## Overview
The inspiration agent has been updated to provide actual Google Maps URLs and Place IDs instead of empty placeholders.

## Changes Made

### 1. Fixed POI Data Structure (`types.py`)
- Fixed syntax error in the `POI` class where `map_url` field was missing its name
- The `map_url` and `place_id` fields are now properly defined as `Optional[str]`

### 2. Updated Prompt Instructions (`prompt.py`)
- Changed the POI agent instructions to clarify that `map_url` and `place_id` should initially be empty strings
- Added note explaining that the `map_tool` will automatically populate these fields with actual Google Maps data

### 3. Updated Model Compatibility (`agent.py`)
- Updated all agents to use `gemini-2.0-flash-live-001` instead of `gemini-2.0-flash-001` for live API compatibility

## How It Works

1. **POI Generation**: When the `poi_agent` generates point of interest suggestions, it initially provides empty strings for `map_url` and `place_id`

2. **Automatic Enhancement**: The `map_tool` is automatically called after POI generation to:
   - Query the Google Places API using the place name and address
   - Retrieve accurate latitude/longitude coordinates
   - Generate proper Google Maps URLs in the format: `https://www.google.com/maps/place/?q=place_id:{place_id}`
   - Populate the `place_id` with the actual Google Places API place ID

3. **Final Result**: Users receive POI suggestions with:
   - Accurate coordinates
   - Working Google Maps links
   - Valid Place IDs for further API integration

## Prerequisites

Make sure you have set up the `GOOGLE_PLACES_API_KEY` environment variable as described in the main README.md file.

## Example Output

After the changes, POI suggestions will include:
```json
{
  "places": [
    {
      "place_name": "Kiyomizu-dera Temple",
      "address": "1-294 Kiyomizu, Higashiyama Ward, Kyoto, 605-0862",
      "lat": "34.9949",
      "long": "135.7851",
      "review_ratings": "4.5",
      "highlights": "Historic Buddhist temple with wooden stage offering city views",
      "image_url": "https://example.com/image.jpg",
      "map_url": "https://www.google.com/maps/place/?q=place_id:ChIJ...",
      "place_id": "ChIJ..."
    }
  ]
}
```

## Testing

To test the Google Maps integration:
1. Ensure your Google Places API key is configured
2. Run the travel concierge agent
3. Ask for destination inspiration (e.g., "suggest some places to visit in Kyoto")
4. The returned POI suggestions should now include working Google Maps URLs and Place IDs