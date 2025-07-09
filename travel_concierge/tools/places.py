# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Wrapper to Google Maps Places API."""

import os
from typing import Dict, List, Any

from google.adk.tools import ToolContext
import requests


class PlacesService:
    """Wrapper to Placees API."""

    def _check_key(self):
        if (
            not hasattr(self, "places_api_key") or not self.places_api_key
        ):  # Either it doesn't exist or is None.
            # https://developers.google.com/maps/documentation/places/web-service/get-api-key
            self.places_api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    def find_place_from_text(self, query: str) -> Dict[str, str]:
        """Fetches place details using a text query."""
        self._check_key()
        places_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        params = {
            "input": query,
            "inputtype": "textquery",
            "fields": "place_id,formatted_address,name,photos,geometry",
            "key": self.places_api_key,
        }

        try:
            response = requests.get(places_url, params=params)
            response.raise_for_status()
            place_data = response.json()

            if not place_data.get("candidates"):
                return {"error": "No places found."}

            # Extract data for the first candidate
            place_details = place_data["candidates"][0]
            place_id = place_details["place_id"]
            place_name = place_details["name"]
            place_address = place_details["formatted_address"]
            photos = self.get_photo_urls(place_details.get("photos", []), maxwidth=400)
            map_url = self.get_map_url(place_id)
            location = place_details["geometry"]["location"]
            lat = str(location["lat"])
            lng = str(location["lng"])

            return {
                "place_id": place_id,
                "place_name": place_name,
                "place_address": place_address,
                "photos": photos,
                "map_url": map_url,
                "lat": lat,
                "lng": lng,
            }

        except requests.exceptions.RequestException as e:
            return {"error": f"Error fetching place data: {e}"}

    def get_photo_urls(self, photos: List[Dict[str, Any]], maxwidth: int = 400) -> List[str]:
        """Extracts photo URLs from the 'photos' list."""
        photo_urls = []
        for photo in photos:
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={maxwidth}&photoreference={photo['photo_reference']}&key={self.places_api_key}"
            photo_urls.append(photo_url)
        return photo_urls

    def get_map_url(self, place_id: str) -> str:
        """Generates the Google Maps URL for a given place ID."""
        return f"https://www.google.com/maps/place/?q=place_id:{place_id}"


# Google Places API
places_service = PlacesService()


def map_tool(key: str, tool_context: ToolContext):
    """
    This is going to inspect the pois stored under the specified key in the state.
    One by one it will retrieve the accurate Lat/Lon from the Map API, if the Map API is available for use.
    Args:
        key: The key under which the POIs are stored.
        tool_context: The ADK tool context.
    Returns:
        The updated state with the full JSON object under the key.
    """
    # Attempt to get POIs from the provided key, with a fallback to 'poi'
    pois_data = tool_context.state.get(key, {})

    # Ensure pois_data is a dictionary, not a string
    if isinstance(pois_data, str):
        pois_data = {}

    if not pois_data or "places" not in pois_data:
        pois_data = tool_context.state.get("poi", {})
        # Ensure this is also a dictionary
        if isinstance(pois_data, str):
            pois_data = {}

    if "places" not in pois_data:
        pois_data["places"] = []

    pois = pois_data["places"]

    # Ensure pois is a list
    if not isinstance(pois, list):
        pois = []
        pois_data["places"] = pois

    for poi in pois:  # The pydantic object types.POI
        # Ensure poi is a dictionary
        if not isinstance(poi, dict):
            continue

        location = poi.get("place_name", "") + ", " + poi.get("address", "")
        result = places_service.find_place_from_text(location)

        # Fill the place holders with verified information.
        poi["place_id"] = result.get("place_id")
        poi["map_url"] = result.get("map_url")

        # Ensure map_url is never empty - create fallback if Google Places API fails
        if not poi.get("map_url") or poi["map_url"] == "":
            # Create a basic Google Maps URL using place name and address
            place_name = poi.get("place_name", "").replace(" ", "+")
            address = poi.get("address", "").replace(" ", "+")
            search_query = f"{place_name}+{address}"
            poi["map_url"] = f"https://www.google.com/maps/search/?api=1&query={search_query}"

        # Update image_url with the first photo found, if available
        if result.get("photos"):
            poi["image_url"] = result["photos"][0]
        # Ensure image_url is never empty - if no Google Places photo, keep the original or use a fallback
        elif not poi.get("image_url") or poi["image_url"] == "":
            # Fallback to a generic image for the destination if no specific image is available
            destination_name = poi.get("place_name", "").split(",")[0].strip()
            poi["image_url"] = f"https://source.unsplash.com/featured/?{destination_name.replace(' ', '+')}"

        if "lat" in result and "lng" in result:
            poi["lat"] = result["lat"]
            poi["long"] = result["lng"]

    return {"places": pois}  # Return the updated pois
