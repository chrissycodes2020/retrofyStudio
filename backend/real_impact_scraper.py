"""
Real Impact.com API Scraper for Retrofy Studio
Pulls authentic luxury goods from TheRealReal via Impact.com API
"""

import requests
import json
import time
import random
from typing import List, Dict
import re
from base64 import b64encode

class RealImpactScraper:
    def __init__(self, api_base_url="http://127.0.0.1:8002"):
        self.api_base_url = api_base_url
        
        # Your real Impact.com credentials
        self.account_sid = "IRFNBGTHkmio2071858ZgWZVTuFxnuqxN1"
        self.auth_token = "xjvbCTKz8svAaz8FUvF~yK.LWJnWVvVS"
        
        # Impact.com API base URL
        self.impact_api_base = "https://api.impact.com"
        
        # Create session with authentication
        self.session = requests.Session()
        
        # Set up Basic Auth (SID as username, Token as password)
        auth_string = f"{self.account_sid}:{self.auth_token}"
        b64_auth = b64encode(auth_string.encode()).decode()
        
        self.session.headers.update({
            'Authorization': f'Basic {b64_auth}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def test_api_connection(self):
        """
        Test the API connection with different possible formats
        """
        print("🔍 Testing Impact.com API connection with different URL formats...")
        
        # Try different possible API base structures
        api_bases = [
            "https://api.impact.com",
            "https://api.impact.com/Advertisers",  # From the curl example
            "https://api.impact.com/Partners", 
            "https://api.impact.com/Mediapartners"
        ]
        
        try:
            for base_url in api_bases:
                print(f"\n🔍 Testing base URL: {base_url}")
                
                # Try different endpoint patterns
                test_endpoints = [
                    f"{base_url}/{self.account_sid}",
                    f"{base_url}/{self.account_sid}/Campaigns",
                    f"{base_url}/{self.account_sid}/Programs", 
                    f"{base_url}/{self.account_sid}/Catalogs"
                ]
                
                for endpoint in test_endpoints:
                    print(f"  Testing: {endpoint}")
                    response = self.session.get(endpoint)
                    print(f"  Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("  ✅ SUCCESS! Found working endpoint!")
                        data = response.json()
                        self.impact_api_base = base_url  # Update base URL
                        return True, data
                    elif response.status_code == 401:
                        print("  ❌ Authentication failed")
                        return False, None
                    elif response.status_code == 403:
                        print("  ⚠️  Access denied (endpoint exists but no permission)")
                    elif response.status_code == 404:
                        print("  ❌ Not found")
                    else:
                        print(f"  ❌ Error: {response.status_code}")
                        if response.text:
                            print(f"    Response: {response.text[:100]}")
            
            print("\n❌ No working endpoints found")
            return False, None
                
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return False, None
    
    def get_therealreal_campaign_id(self):
        """
        Find TheRealReal's campaign ID and show all available campaigns
        """
        print("🔍 Checking available campaigns/programs...")
        
        try:
            # Use the working endpoint we found
            url = f"{self.impact_api_base}/{self.account_sid}/Campaigns"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('Items', [])
                
                print(f"✅ Found {len(items)} available campaigns/programs:")
                
                if items:
                    for item in items[:10]:  # Show first 10
                        name = item.get('Name', 'Unknown')
                        advertiser = item.get('AdvertiserName', 'Unknown')
                        campaign_id = item.get('Id', 'Unknown')
                        status = item.get('Status', 'Unknown')
                        
                        print(f"  📋 {advertiser}: {name}")
                        print(f"      ID: {campaign_id} | Status: {status}")
                        
                        # Check if it's TheRealReal
                        if 'realreal' in name.lower() or 'real real' in name.lower() or 'realreal' in advertiser.lower():
                            print(f"  🎯 Found TheRealReal! Campaign ID: {campaign_id}")
                            return campaign_id
                        
                        print()  # Empty line for readability
                    
                    if len(items) > 10:
                        print(f"  ... and {len(items) - 10} more campaigns")
                else:
                    print("  📭 No campaigns found - you may need to apply to affiliate programs")
                
                return None
            else:
                print(f"❌ Error fetching campaigns: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def get_product_catalog(self, campaign_id=None, limit=50):
        """
        Get products from Impact.com catalog - PUBLISHER VERSION
        """
        print(f"📦 Fetching products from Impact.com API (Publisher account)...")
        
        try:
            # Publisher endpoints for getting product data
            endpoints_to_try = [
                f"{self.impact_api_base}/Publishers/{self.account_sid}/Ads",
                f"{self.impact_api_base}/Publishers/{self.account_sid}/Catalogs",
                f"{self.impact_api_base}/Publishers/{self.account_sid}/ProductCatalog"
            ]
            
            if campaign_id:
                endpoints_to_try.insert(0, 
                    f"{self.impact_api_base}/Publishers/{self.account_sid}/Campaigns/{campaign_id}/Ads"
                )
                endpoints_to_try.insert(1,
                    f"{self.impact_api_base}/Publishers/{self.account_sid}/Campaigns/{campaign_id}/Catalogs"
                )
            
            for endpoint in endpoints_to_try:
                print(f"🔍 Trying endpoint: {endpoint}")
                
                params = {
                    'PageSize': limit,
                    'Page': 1
                }
                
                response = self.session.get(endpoint, params=params)
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('Items', [])
                    
                    if items:
                        print(f"✅ Found {len(items)} items!")
                        print("Sample item keys:", list(items[0].keys()) if items else "None")
                        return items
                    else:
                        print("📭 Endpoint returned empty results")
                elif response.status_code == 404:
                    print("❌ Endpoint not found")
                elif response.status_code == 403:
                    print("❌ Access denied (may need approval for this program)")
                else:
                    print(f"❌ Error {response.status_code}: {response.text[:200]}")
            
            print("❌ No products found from any endpoint")
            return []
            
        except Exception as e:
            print(f"❌ Error fetching products: {str(e)}")
            return []
    
    def parse_impact_product(self, item) -> Dict:
        """
        Convert Impact.com product data to Retrofy format
        """
        try:
            # Extract fields (Impact.com structure may vary)
            title = item.get('Name', '') or item.get('AdName', '') or item.get('ProductName', '')
            description = item.get('Description', '') or item.get('AdDescription', '')
            price_str = item.get('Price', '') or item.get('SalePrice', '') or item.get('Cost', '')
            image_url = item.get('ImageUrl', '') or item.get('ThumbnailUrl', '')
            product_url = item.get('TrackingUrl', '') or item.get('Url', '') or item.get('DestinationUrl', '')
            
            # Parse price
            price = 0.0
            if price_str:
                # Remove currency symbols and extract number
                price_match = re.search(r'[\d,]+\.?\d*', str(price_str))
                if price_match:
                    price = float(price_match.group().replace(',', ''))
            
            # Extract brand from title or description
            brand = self.extract_brand_from_text(title + ' ' + description)
            
            # Categorize item
            category = self.categorize_item(title + ' ' + description)
            
            # Extract color
            color = self.extract_color(title + ' ' + description)
            
            product = {
                "title": self.clean_text(title),
                "brand": brand,
                "category": category,
                "color": color,
                "description": self.clean_text(description),
                "price": price,
                "image_url": image_url,
                "platform_name": "TheRealReal",
                "product_url": product_url
            }
            
            return product
            
        except Exception as e:
            print(f"Error parsing product: {str(e)}")
            return None
    
    def extract_brand_from_text(self, text: str) -> str:
        """Extract brand from text"""
        luxury_brands = [
            'Chanel', 'Louis Vuitton', 'Gucci', 'Hermès', 'Hermes', 'Prada', 'Bottega Veneta',
            'Saint Laurent', 'YSL', 'Balenciaga', 'Celine', 'Dior', 'Fendi', 'Givenchy',
            'Valentino', 'Tom Ford', 'Burberry', 'Cartier', 'Rolex', 'Tiffany',
            'Van Cleef', 'Bulgari', 'Christian Louboutin', 'Jimmy Choo', 'Manolo Blahnik',
            'Bottega', 'Alexander McQueen', 'Versace', 'Armani', 'Dolce'
        ]
        
        text_upper = text.upper()
        
        for brand in luxury_brands:
            if brand.upper() in text_upper:
                return brand
        
        # Extract first word as fallback
        words = text.split()
        return words[0] if words else "Unknown"
    
    def categorize_item(self, text: str) -> str:
        """Categorize based on text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['bag', 'purse', 'tote', 'clutch', 'satchel', 'hobo', 'handbag']):
            return 'handbags'
        elif any(word in text_lower for word in ['shoe', 'pump', 'heel', 'boot', 'sneaker', 'sandal', 'loafer']):
            return 'shoes'
        elif any(word in text_lower for word in ['watch', 'bracelet', 'necklace', 'ring', 'earring', 'jewelry']):
            return 'jewelry'
        elif any(word in text_lower for word in ['scarf', 'belt', 'wallet', 'sunglasses', 'accessory']):
            return 'accessories'
        elif any(word in text_lower for word in ['dress', 'shirt', 'jacket', 'coat', 'sweater', 'top']):
            return 'clothing'
        else:
            return 'other'
    
    def extract_color(self, text: str) -> str:
        """Extract color from text"""
        colors = ['black', 'white', 'brown', 'tan', 'beige', 'red', 'blue', 'navy', 
                 'green', 'pink', 'purple', 'gold', 'silver', 'grey', 'gray', 'yellow', 'orange']
        
        text_lower = text.lower()
        
        for color in colors:
            if color in text_lower:
                return color
        
        return 'multicolor'
    
    def clean_text(self, text: str) -> str:
        """Clean text"""
        if not text:
            return ""
        
        text = ' '.join(text.split())
        text = re.sub(r'[^\w\s\-\(\)\.\,]', '', text)
        return text.strip()
    
    def send_to_api(self, products: List[Dict]) -> bool:
        """Send products to Retrofy API"""
        if not products:
            print("No products to send to API")
            return False
        
        try:
            url = f"{self.api_base_url}/seed_products"
            
            print(f"Sending {len(products)} products to Retrofy API...")
            
            response = requests.post(url, json=products)
            response.raise_for_status()
            
            print("✅ Products successfully added to Retrofy database!")
            return True
            
        except Exception as e:
            print(f"❌ Error sending products to API: {str(e)}")
            return False
    
    def run_real_scraping_session(self, limit=20):
        """
        Run real scraping session with Impact.com API
        """
        print("🚀 Starting REAL Impact.com API scraping session...")
        print("💎 Getting authentic luxury data from TheRealReal!")
        
        # Test API connection
        success, campaigns_data = self.test_api_connection()
        if not success:
            print("❌ Cannot connect to Impact.com API")
            return False
        
        # Find TheRealReal campaign
        campaign_id = self.get_therealreal_campaign_id()
        
        # Get products
        raw_products = self.get_product_catalog(campaign_id, limit)
        
        if not raw_products:
            print("❌ No products found")
            return False
        
        # Parse products
        products = []
        for item in raw_products:
            product = self.parse_impact_product(item)
            if product and product.get('title'):
                products.append(product)
        
        if products:
            print(f"\n📦 Successfully parsed {len(products)} luxury products!")
            
            # Show samples
            print("\n🔍 Sample products found:")
            for i, product in enumerate(products[:3]):
                print(f"{i+1}. {product['brand']} - {product['title']} - ${product['price']}")
            
            # Send to Retrofy API
            success = self.send_to_api(products)
            
            if success:
                print(f"\n🎉 REAL SCRAPING COMPLETE! {len(products)} authentic luxury products added to Retrofy!")
                print("🔥 Your luxury aggregator now has REAL inventory!")
            else:
                print("\n❌ Failed to add products to database")
        else:
            print("\n❌ No valid products could be parsed")
        
        return len(products) > 0


# Usage
if __name__ == "__main__":
    scraper = RealImpactScraper()
    scraper.run_real_scraping_session(limit=30)  # Get 30 products