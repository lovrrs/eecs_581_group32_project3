# File: src/places_api.py
# Description: Google Places API integration for points of interest
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-11-20

from pyparsing import Path
import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)  # Load environment variables from .env file
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

class PlacesAPI:
    def __init__(self):
        self.api_key = GOOGLE_PLACES_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    def search_places(self, query:str, location:str=None) -> List[Dict]:
        """
        Search for points of interest using Google Places API
        
        Args:
            query: search term (e.g., "restaurants", "museums", "parks")
            location: optional location string (e.g., "Seattle, WA")
            
        Returns:
            List of places matching the query
        """

        if not self.api_key:
            raise ValueError("Google Places API key is not set or is invalid.")
        
        # build search query
        search_query = query
        if location:
            search_query = f"{query} in {location}"
        else:
            search_query = f"{query}"

        try:
            params = {
                'query': search_query,
                'key': self.api_key,
            }

            # make API request
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status() # raise error for bad responses

            data = response.json() # parse JSON response

            # check for API errors
            if data.get('status') != 'OK':
                error_msg = data.get('error_message', 'Unknown API error.')
                raise Exception(f"Google Places API error: {data.get('status')} - {error_msg}")
            
            places = [] # list to hold place results
            for place in data.get('results', [])[:10]: # limit to top 10 results
                places.append({
                    'name': place.get('name', 'Unknown'),
                    'address': place.get('formatted_address', 'Address not available'),
                    'rating': place.get('rating', 'No rating'),
                    'types': place.get('types', []),
                    'place_id': place.get('place_id'),
                })
            return places
        
        except requests.RequestException as e:
            raise Exception(f"Error connecting to Google Places API: {e}")
        except Exception as e:
            raise Exception(f"An error occurred: {e}")
        
def display_places(places):
    """Display places in a formatted list"""
    if not places:
        print("No places found.")
        return
    
    print("\n" + "="*50)
    print("POINTS OF INTEREST:")
    print("="*50 + "\n")

    for idx, place in enumerate(places, 1):
        rating = place['rating'] if place['rating'] != 'No rating' else 'N/A'
        types = ', '.join(place['types'][:3]) # show first 3 types

        print(f"{idx:2d}. {place['name']}")
        print(f"        ⚲ {place['address']}")
        print(f"        ☆ Rating: {rating} | ♒︎ Types: {types}")
        print()
    
    print("="*50 + "\n")

def suggest_categories_from_places(place_types: List[str]) -> str:
    """
    Suggest task categories based on place types
    
    Args:
        place_types: list of place types from Google Places API
        
    Returns:
        List of suggested categories
    """
    category_map = {
        'restaurant': 'Meals',
        'cafe': 'Meals',
        'museum': 'Leisure',
        'park': 'Leisure',
        'gym': 'Health',
        'library': 'Study',
        'shopping_mall': 'Leisure',
        'movie_theater': 'Leisure',
        'bar': 'Leisure',
        'spa': 'Health',
        'movie_theater': 'Leisure',
        'night_club': 'Leisure',
        'zoo': 'Leisure',
        'art_gallery': 'Leisure',
        'amusement_park': 'Leisure',
        'tourist_attraction': 'Leisure',
        'aquarium': 'Leisure',
        'stadium': 'Leisure',
        'dessert_shop': 'Meals',
        'bakery': 'Meals',
        'coffee_shop': 'Meals',
        'beach': 'Leisure',
    }
    
    for ptype in place_types:
        if ptype in category_map:
            return category_map[ptype]
    
    return 'Leisure'  # default category