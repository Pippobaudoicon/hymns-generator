"""Data scraper for Italian hymns from churchofjesuschrist.org."""

import json
import requests
import logging
from pathlib import Path
from urllib.parse import quote
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class HymnScraper:
    """Scraper for Italian hymns from the Church website."""
    
    BASE_URL = "https://www.churchofjesuschrist.org/media/music/api"
    
    def __init__(self, output_dir: str = "data"):
        """Initialize the scraper."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def _build_api_url(self) -> str:
        """Build the API URL for fetching Italian hymns."""
        identifier = {
            "lang": "ita",
            "limit": 500,
            "offset": 0,
            "orderByKey": ["bookSongPosition"],
            "bookQueryList": ["hymns"]
        }
        
        params = {
            "type": "songsFilteredList",
            "lang": "ita",
            "identifier": quote(json.dumps(identifier)),
            "batchSize": 20
        }
        
        return f"{self.BASE_URL}?type={params['type']}&lang={params['lang']}&identifier={params['identifier']}&batchSize={params['batchSize']}"
    
    def fetch_hymns_data(self) -> List[Dict[str, Any]]:
        """Fetch hymns data from the API."""
        try:
            url = self._build_api_url()
            logger.info(f"Fetching hymns from: {url}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            hymns_data = data.get('data', [])
            
            logger.info(f"Successfully fetched {len(hymns_data)} hymns")
            return hymns_data
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch hymns data: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            raise
    
    def save_full_data(self, filename: str = "italian_hymns_full.json") -> Path:
        """Save full hymns data to JSON file."""
        hymns_data = self.fetch_hymns_data()
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(hymns_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved full hymns data to: {output_path}")
            return output_path
            
        except IOError as e:
            logger.error(f"Failed to save full data: {e}")
            raise
    
    def save_simplified_data(self, filename: str = "italian_hymns.csv") -> Path:
        """Save simplified hymns data to CSV file."""
        hymns_data = self.fetch_hymns_data()
        output_path = self.output_dir / filename
        
        try:
            import csv
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if not hymns_data:
                    return output_path
                
                fieldnames = ['number', 'title', 'category', 'tags', 'url']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in hymns_data:
                    row = {
                        'number': item.get('songNumber', ''),
                        'title': item.get('title', ''),
                        'category': item.get('bookSectionTitle', ''),
                        'tags': ', '.join(item.get('tags', [])),
                        'url': item.get('assets', [{}])[0].get('mediaObject', {}).get('distributionUrl', '') if item.get('assets') else ''
                    }
                    writer.writerow(row)
            
            logger.info(f"Saved simplified hymns data to: {output_path}")
            return output_path
            
        except ImportError:
            logger.error("CSV module not available")
            raise
        except IOError as e:
            logger.error(f"Failed to save simplified data: {e}")
            raise


def main():
    """Main function for running the scraper."""
    logging.basicConfig(level=logging.INFO)
    
    scraper = HymnScraper()
    
    try:
        # Save both full and simplified data
        scraper.save_full_data()
        scraper.save_simplified_data()
        print("Successfully scraped and saved hymns data!")
        
    except Exception as e:
        print(f"Error scraping hymns data: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
