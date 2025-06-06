"""
Service for handling image-related operations.
"""
import os
import json
from typing import List
import requests
from dotenv import load_dotenv

from ..utils.config import Config


class ImageService:
    """Service for handling image operations."""

    def __init__(self, config: Config):
        """Initialize the image service.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.test_images = [
            "https://i0.wp.com/www.thejudyroom.com/wp-content/uploads/2023/06/Munchkinland-Set-1-FX.jpg?ssl=1",
            "https://c8.alamy.com/comp/DWEEG0/judy-garland-on-set-of-the-film-the-wizard-of-oz-1939-DWEEG0.jpg",
            "http://farm4.staticflickr.com/3417/4626284019_9215b506bb_z.jpg"
        ]

    def fetch_images(self, keywords: str, max_results: int = 5) -> List[str]:
        """Fetch images using Google Custom Search API or return test images.
        
        Args:
            keywords: Search keywords
            max_results: Maximum number of results to return
            
        Returns:
            List of image URLs
        """
        if self.config.mode == 'test':
            return self._get_test_images(max_results)
        return self._fetch_from_google(keywords, max_results)

    def _get_test_images(self, max_results: int) -> List[str]:
        """Get test images for development.
        
        Args:
            max_results: Maximum number of images to return
            
        Returns:
            List of test image URLs
        """
        print("Using test mode with predefined images...")
        images = self.test_images[:max_results]
        for idx, url in enumerate(images, 1):
            print(f"{idx}. URL: {url}\n")
        print(f"Successfully loaded {len(images)} test images")
        return images

    def _fetch_from_google(self, keywords: str, max_results: int) -> List[str]:
        """Fetch images from Google Custom Search API.
        
        Args:
            keywords: Search keywords
            max_results: Maximum number of results to return
            
        Returns:
            List of image URLs
        """
        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            cx = os.getenv('GOOGLE_CX')
            
            if not api_key or not cx:
                print("Error: Google API credentials not found in environment variables")
                return []
            
            base_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cx,
                'q': keywords,
                'searchType': 'image',
                'num': max_results,
                'safe': 'medium',
                'imgSize': 'large'
            }
            
            print(f"Searching for '{keywords}'...")
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            results = response.json()
            if 'items' not in results:
                print("No images found")
                return []
            
            images = []
            for idx, item in enumerate(results['items'], 1):
                print(f"{idx}. Title: {item['title']}")
                print(f"   URL: {item['link']}\n")
                images.append(item['link'])
            
            print(f"Successfully fetched {len(images)} images")
            return images
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing response: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return [] 