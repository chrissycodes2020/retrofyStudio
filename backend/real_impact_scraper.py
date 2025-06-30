"""
Real Impact.com API Scraper for Retrofy Studio
Pulls authentic luxury goods from TheRealReal via Impact.com API
FIXED VERSION - Uses correct catalog endpoints
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
        Test the API connection - FIXED VERSION
        """
        print("🔍 Testing Impact.com API connection...")
        
        try:
            # Test the working endpoint we found
            url = f"{self.impact_api_base}/Mediapartners/{self.account_sid}/Campaigns"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API connection successful!")
                return True, data
            else:
                print(f"❌ API connection failed: {response.status_code}")
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
            url = f"{self.impact_api_base}/Mediapartners/{self.account_sid}/Campaigns"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                campaigns = data.get('Campaigns', [])
                
                print(f"✅ Found {len(campaigns)} available campaigns:")
                
                if campaigns:
                    for campaign in campaigns:
                        name = campaign.get('CampaignName', 'Unknown')
                        advertiser = campaign.get('AdvertiserName', 'Unknown')
                        campaign_id = campaign.get('CampaignId', 'Unknown')
                        status = campaign.get('ContractStatus', 'Unknown')
                        
                        print(f"  📋 {advertiser}: {name}")
                        print(f"      ID: {campaign_id} | Status: {status}")
                        
                        # Check if it's TheRealReal
                        if 'realreal' in name.lower() or 'real real' in name.lower() or 'realreal' in advertiser.lower():
                            print(f"  🎯 Found TheRealReal! Campaign ID: {campaign_id}")
                            return campaign_id
                        
                        print()  # Empty line for readability
                else:
                    print("  📭 No campaigns found")
                
                return None
            else:
                print(f"❌ Error fetching campaigns: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def get_product_catalog(self, campaign_id=None, limit=50):
        """
        Get products from Impact.com catalog - FIXED VERSION
        """
        print(f"📦 Fetching products from Impact.com Catalogs API...")
        
        try:
            # FIXED: Use the correct endpoint that works
            catalog_url = f"{self.impact_api_base}/Mediapartners/{self.account_sid}/Catalogs"
            
            print(f"🔍 Getting available catalogs...")
            response = self.session.get(catalog_url)
            
            if response.status_code != 200:
                print(f"❌ Error getting catalogs: {response.status_code}")
                return []
            
            catalog_data = response.json()
            catalogs = catalog_data.get('Catalogs', [])
            
            print(f"Found {len(catalogs)} catalogs")
            
            # Find TheRealReal catalog
            realreal_catalog = None
            for catalog in catalogs:
                if 'realreal' in str(catalog).lower():
                    realreal_catalog = catalog
                    print(f"🎯 Found TheRealReal catalog: {catalog.get('Id')}")
                    break
            
            if not realreal_catalog:
                print("❌ TheRealReal catalog not found")
                return []
            
            # Get products from TheRealReal catalog
            catalog_id = realreal_catalog.get('Id')
            products_url = f"{self.impact_api_base}/Mediapartners/{self.account_sid}/Catalogs/{catalog_id}/Items"
            
            params = {
                'PageSize': limit,
                'Page': 1
            }
            
            print(f"🔍 Fetching {limit} products from catalog {catalog_id}...")
            products_response = self.session.get(products_url, params=params)
            
            if products_response.status_code == 200:
                products_data = products_response.json()
                items = products_data.get('Items', [])
                total = products_data.get('@total', 0)
                
                print(f"✅ Found {len(items)} items (out of {total} total products)!")
                return items
            else:
                print(f"❌ Error fetching products: {products_response.status_code}")
                print(f"Response: {products_response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching products: {str(e)}")
            return []
    
    def parse_impact_product(self, item) -> Dict:
        """
        Convert Impact.com product data to Retrofy format - FIXED VERSION
        """
        try:
            # Extract fields from the actual Impact.com structure
            title = item.get('Name', '')
            description = item.get('Description', '')
            price_str = item.get('CurrentPrice', '') or item.get('OriginalPrice', '')
            image_url = item.get('ImageUrl', '')
            product_url = item.get('Url', '')
            
            # Impact.com specific fields
            brand = item.get('Manufacturer', '') or item.get('Text1', '')
            category = item.get('Category', '') or item.get('SubCategory', '')
            color = item.get('Colors', '')
            size = item.get('Size', '')
            condition = item.get('Condition', '')
            material = item.get('Material', '')
            
            # Parse price
            price = 0.0
            if price_str:
                # Remove currency symbols and extract number
                price_match = re.search(r'[\d,]+\.?\d*', str(price_str))
                if price_match:
                    price = float(price_match.group().replace(',', ''))
            
            # If brand is empty, extract from title or description
            if not brand:
                brand = self.extract_brand_from_text(title + ' ' + description)
            
            # If category is empty, categorize based on text
            if not category:
                category = self.categorize_item(title + ' ' + description)
            else:
                # Clean up the category
                category = category.lower().replace(' ', '_')
            
            # If color is empty, extract from text
            if not color:
                color = self.extract_color(title + ' ' + description)
            
            # Build enhanced description
            enhanced_desc = description
            if condition:
                enhanced_desc += f" Condition: {condition}."
            if material:
                enhanced_desc += f" Material: {material}."
            if size:
                enhanced_desc += f" Size: {size}."
            
            product = {
                "title": self.clean_text(title),
                "brand": self.clean_text(brand),
                "category": category,
                "color": self.clean_text(color),
                "description": self.clean_text(enhanced_desc),
                "price": price,
                "image_url": image_url,
                "platform_name": "TheRealReal",
                "product_url": product_url,
                # Additional metadata
                "condition": condition,
                "material": material,
                "size": size
            }
            
            return product
            
        except Exception as e:
            print(f"Error parsing product: {str(e)}")
            return None
    
    def extract_brand_from_text(self, text: str) -> str:
        """Extract brand from text"""
        # Handle cases where text might be a list
        if isinstance(text, list):
            text = ' '.join(str(item) for item in text)
        elif not isinstance(text, str):
            text = str(text)
            
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
        
        # Handle cases where text might be a list
        if isinstance(text, list):
            text = ' '.join(str(item) for item in text)
        elif not isinstance(text, str):
            text = str(text)
        
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
        Run real scraping session with Impact.com API - FIXED VERSION
        """
        print("🚀 Starting REAL Impact.com API scraping session...")
        print("💎 Getting authentic luxury data from TheRealReal!")
        
        # Test API connection
        success, campaigns_data = self.test_api_connection()
        if not success:
            print("❌ Cannot connect to Impact.com API")
            return False
        
        # Find TheRealReal campaign (for reference)
        campaign_id = self.get_therealreal_campaign_id()
        
        # Get products using the FIXED catalog method
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