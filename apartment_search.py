#!/usr/bin/env python3
"""
South Goa Apartment Search Tool
Searches for newly constructed or under-construction 3 BHK apartments
in specified areas: Colva, Betalbatim, Utorda, Seraulim, Benaulim, Varca
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import List, Dict
import time

# Target areas in South Goa
TARGET_AREAS = [
    "Colva",
    "Betalbatim", 
    "Utorda",
    "Seraulim",
    "Benaulim",
    "Varca"
]

class ApartmentSearch:
    def __init__(self):
        self.results = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def search_99acres(self, area: str) -> List[Dict]:
        """Search 99acres.com for apartments"""
        results = []
        try:
            # Construct search URL
            search_query = f"3 BHK apartment {area} South Goa"
            url = f"https://www.99acres.com/search/property/buy/apartment/{area.lower()}-goa"
            
            print(f"Searching 99acres for {area}...")
            # Note: Actual scraping would require handling pagination and dynamic content
            # This is a template structure
            
        except Exception as e:
            print(f"Error searching 99acres for {area}: {e}")
        
        return results
    
    def search_magicbricks(self, area: str) -> List[Dict]:
        """Search MagicBricks for apartments"""
        results = []
        try:
            print(f"Searching MagicBricks for {area}...")
            # Template for MagicBricks search
        except Exception as e:
            print(f"Error searching MagicBricks for {area}: {e}")
        
        return results
    
    def search_housing(self, area: str) -> List[Dict]:
        """Search Housing.com for apartments"""
        results = []
        try:
            print(f"Searching Housing.com for {area}...")
            # Template for Housing.com search
        except Exception as e:
            print(f"Error searching Housing.com for {area}: {e}")
        
        return results
    
    def search_all_areas(self):
        """Search all target areas"""
        print(f"\n{'='*60}")
        print("SOUTH GOA APARTMENT SEARCH")
        print(f"{'='*60}")
        print(f"Searching for: 3 BHK Apartments (New/Under Construction)")
        print(f"Areas: {', '.join(TARGET_AREAS)}")
        print(f"{'='*60}\n")
        
        for area in TARGET_AREAS:
            print(f"\n📍 Searching in {area}...")
            
            # Search multiple platforms
            area_results = []
            
            # 99acres results
            results_99 = self.search_99acres(area)
            area_results.extend(results_99)
            
            # MagicBricks results
            results_mb = self.search_magicbricks(area)
            area_results.extend(results_mb)
            
            # Housing.com results
            results_h = self.search_housing(area)
            area_results.extend(results_h)
            
            # Add area info to each result
            for result in area_results:
                result['area'] = area
                result['search_date'] = datetime.now().isoformat()
            
            self.results.extend(area_results)
            print(f"Found {len(area_results)} listings in {area}")
            
            time.sleep(1)  # Be respectful with requests
    
    def filter_new_construction(self, results: List[Dict]) -> List[Dict]:
        """Filter for newly constructed or under-construction properties"""
        filtered = []
        keywords = ['new', 'under construction', 'ready to move', 'newly constructed', 
                   'under-construction', 'new project', 'pre-launch']
        
        for result in results:
            description = result.get('description', '').lower()
            title = result.get('title', '').lower()
            status = result.get('status', '').lower()
            
            if any(keyword in description or keyword in title or keyword in status 
                   for keyword in keywords):
                filtered.append(result)
        
        return filtered
    
    def save_results(self, filename: str = 'apartment_results.json'):
        """Save search results to JSON file"""
        filtered_results = self.filter_new_construction(self.results)
        
        output = {
            'search_criteria': {
                'bhk': '3 BHK',
                'areas': TARGET_AREAS,
                'property_type': 'Apartment',
                'status': 'New/Under Construction',
                'search_date': datetime.now().isoformat()
            },
            'total_results': len(filtered_results),
            'results': filtered_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved to {filename}")
        print(f"Total listings found: {len(filtered_results)}")
    
    def print_summary(self):
        """Print summary of search results"""
        filtered = self.filter_new_construction(self.results)
        
        print(f"\n{'='*60}")
        print("SEARCH SUMMARY")
        print(f"{'='*60}")
        print(f"Total listings found: {len(filtered)}")
        
        # Group by area
        by_area = {}
        for result in filtered:
            area = result.get('area', 'Unknown')
            by_area[area] = by_area.get(area, 0) + 1
        
        print(f"\nBreakdown by area:")
        for area, count in sorted(by_area.items()):
            print(f"  {area}: {count} listings")
        print(f"{'='*60}\n")


def main():
    """Main function"""
    searcher = ApartmentSearch()
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   South Goa 3 BHK Apartment Search Tool                 ║
    ║   Areas: Colva, Betalbatim, Utorda, Seraulim,           ║
    ║          Benaulim, Varca                                 ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Run search
    searcher.search_all_areas()
    
    # Print summary
    searcher.print_summary()
    
    # Save results
    searcher.save_results()
    
    print("\n💡 Next Steps:")
    print("   1. Review the apartment_results.json file")
    print("   2. Visit property websites directly for detailed information")
    print("   3. Contact builders/agents for site visits")
    print("   4. Verify RERA registration for under-construction projects")


if __name__ == "__main__":
    main()
