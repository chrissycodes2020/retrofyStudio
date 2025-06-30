"""
Real Impact.com API Scraper for Retrofy Studio
Pulls authentic luxury goods from TheRealReal via Impact.com API
FIXED VERSION - Uses correct catalog endpoints and brand extraction with DEBUG
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
        Convert Impact.com product data to Retrofy format - FIXED VERSION WITH DEBUG
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
            
            # DEBUG OUTPUT
            print(f"DEBUG - Raw brand from API: '{brand}'")
            print(f"DEBUG - Title: '{title}'")

            # Parse price
            price = 0.0
            if price_str:
                # Remove currency symbols and extract number
                price_match = re.search(r'[\d,]+\.?\d*', str(price_str))
                if price_match:
                    price = float(price_match.group().replace(',', ''))

            # FIXED: Validate brand and extract from title if invalid
            validated_brand = self.extract_brand_from_title_or_validate(title, brand)
            print(f"DEBUG - Brand after validation: '{validated_brand}'")

            # If still no valid brand, try description as fallback
            if validated_brand == "Unknown" or not validated_brand:
                validated_brand = self.extract_brand_from_text(description)
                print(f"DEBUG - Extracted brand from description: '{validated_brand}'")

            print(f"DEBUG - Brand before clean_text: '{validated_brand}'")
            final_brand = self.clean_text(validated_brand)
            print(f"DEBUG - Brand after clean_text: '{final_brand}'")
            
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
                "brand": final_brand,  # Using the final_brand after clean_text
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
            
            print(f"DEBUG - FINAL PRODUCT BRAND: '{product['brand']}'")
            
            return product
            
        except Exception as e:
            print(f"Error parsing product: {str(e)}")
            return None
    
    def extract_brand_from_title_or_validate(self, title, brand):
        """Extract brand from title when API brand is invalid (like '0', '1', etc.)"""
        
        # Invalid brand values that we should ignore
        invalid_brands = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '', 'null', 'undefined', 'None']
        
        # Check if brand is invalid
        if not brand or str(brand).strip() in invalid_brands:
            print(f"DEBUG - Invalid brand '{brand}', extracting from title: '{title}'")
            
            # Use your existing extract_brand_from_text method
            extracted_brand = self.extract_brand_from_text(title)
            print(f"DEBUG - Extracted brand from title: {extracted_brand}")
            return extracted_brand
        
        return brand
    
    def extract_brand_from_text(self, text: str) -> str:
        """Extract brand from text - prioritize title field with DEBUG"""
        print(f"DEBUG - extract_brand_from_text called with: '{text}'")
        
        # Handle cases where text might be a list
        if isinstance(text, list):
            text = ' '.join(str(item) for item in text)
        elif not isinstance(text, str):
            text = str(text)
        
        if not text or text.strip() == "":
            print(f"DEBUG - Text is empty, returning Unknown")
            return "Unknown"
        
        print(f"DEBUG - Processing text: '{text}'")
            
        luxury_brands = [
            'Chanel', 'Louis Vuitton', 'Gucci', 'Hermès', 'Hermes', 'Prada', 'Bottega Veneta',
            'Saint Laurent', 'YSL', 'Balenciaga', 'Celine', 'Dior', 'Fendi', 'Givenchy',
            'Valentino', 'Tom Ford', 'Burberry', 'Cartier', 'Rolex', 'Tiffany',
            'Van Cleef', 'Bulgari', 'Christian Louboutin', 'Jimmy Choo', 'Manolo Blahnik',
            'Bottega', 'Alexander McQueen', 'Versace', 'Armani', 'Dolce', 'Isabel Marant',
            'Jean Paul Gaultier', 'Miu Miu', 'Michael Kors', 'Jason Wu', 'Henry Beguelin',
            'For Love & Lemons', 'Sachin & Babi', 'Momoni', 'Mercedes Castillo',
            'I. Reiss', 'Jil Sander', 'Isaia', 'IWC'
        ]
        
        text_upper = text.upper()
        print(f"DEBUG - Text in uppercase: '{text_upper}'")
        
        # Check for exact brand matches first
        for brand in luxury_brands:
            if brand.upper() in text_upper:
                print(f"DEBUG - Found luxury brand match: '{brand}'")
                return brand
        
        print(f"DEBUG - No luxury brand found, using fallback logic")
        
        # If no luxury brand found, try to extract a reasonable brand name
        # Clean the text first
        cleaned_text = text.strip()
        print(f"DEBUG - Cleaned text: '{cleaned_text}'")
        
        # If the title/text is just a brand name (common case), return it
        if len(cleaned_text.split()) <= 3 and not any(char.isdigit() for char in cleaned_text):
            print(f"DEBUG - Short text without digits, returning as brand: '{cleaned_text}'")
            return cleaned_text
        
        # Extract first meaningful word(s) as fallback
        words = cleaned_text.split()
        print(f"DEBUG - Words in text: {words}")
        
        if words:
            # Skip common prefixes and get the actual brand
            first_word = words[0]
            print(f"DEBUG - First word: '{first_word}'")
            # Don't return single digits or very short strings as brand names
            if len(first_word) > 1 and not first_word.isdigit():
                print(f"DEBUG - Returning first word as brand: '{first_word}'")
                return first_word
        
        print(f"DEBUG - All fallbacks failed, returning Unknown")
        return "Unknown"
    
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
        """Send products to Retrofy API or save to file as backup"""
        if not products:
            print("No products to send")
            return False
        
        # Try API first
        try:
            url = f"{self.api_base_url}/seed_products"
            print(f"Sending {len(products)} products to Retrofy API...")
            response = requests.post(url, json=products)
            response.raise_for_status()
            print("✅ Products successfully added to Retrofy database!")
            return True
            
        except Exception as e:
            print(f"❌ Error sending products to API: {str(e)}")
            print("💾 Saving products to file instead...")
            
            # Save to JSON file as backup
            try:
                filename = f"therealreal_products_{int(time.time())}.json"
                with open(filename, 'w') as f:
                    json.dump(products, f, indent=2)
                print(f"✅ Products saved to {filename}")
                print(f"🔥 {len(products)} authentic luxury products scraped successfully!")
                return True
            except Exception as file_error:
                print(f"❌ Error saving to file: {str(file_error)}")
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


# DEBUG TEST
if __name__ == "__main__":
    scraper = RealImpactScraper()
    
    # Test one real product to see the debug output
    print("🧪 TESTING ONE REAL PRODUCT:")
    raw_products = scraper.get_product_catalog(limit=1)
    if raw_products:
        item = raw_products[0]
        print(f"Raw title from API: '{item.get('Name', '')}'")
        
        parsed_product = scraper.parse_impact_product(item)
        if parsed_product:
            print(f"Final brand in product: '{parsed_product['brand']}'")
    
    # Uncomment to run full scraping session
    # scraper.run_real_scraping_session(limit=30)