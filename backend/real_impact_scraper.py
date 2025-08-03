"""
Real Impact.com API Scraper for Retrofy Studio
Pulls authentic luxury goods from TheRealReal via Impact.com API
DEBUG VERSION - Includes debugging to see what API is actually returning
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
    
    def debug_api_responses(self):
        """DEBUG: See what the API is actually returning across different pages"""
        print("🔍 DEBUGGING API RESPONSES...")
        print("=" * 60)
        
        try:
            catalog_url = f"{self.impact_api_base}/Mediapartners/{self.account_sid}/Catalogs"
            response = self.session.get(catalog_url)
            
            if response.status_code != 200:
                print(f"❌ Error getting catalogs: {response.status_code}")
                return
            
            catalog_data = response.json()
            catalogs = catalog_data.get('Catalogs', [])
            
            print(f"📋 Found {len(catalogs)} total catalogs")
            
            # Show ALL catalogs first
            print("\n🔍 ALL AVAILABLE CATALOGS:")
            for i, catalog in enumerate(catalogs):
                print(f"  {i+1}. {catalog}")
                
            # Find TheRealReal catalog
            realreal_catalog = None
            for catalog in catalogs:
                if 'realreal' in str(catalog).lower():
                    realreal_catalog = catalog
                    print(f"\n🎯 FOUND THEREALREAL CATALOG: {catalog}")
                    break
            
            if not realreal_catalog:
                print("❌ No TheRealReal catalog found")
                return
            
            catalog_id = realreal_catalog.get('Id')
            products_url = f"{self.impact_api_base}/Mediapartners/{self.account_sid}/Catalogs/{catalog_id}/Items"
            
            print(f"\n📦 TESTING PRODUCTS FROM CATALOG {catalog_id}")
            print("=" * 60)
            
            # Test multiple pages to see if we get different products
            pages_to_test = [1, 2, 3, 5, 10, 15, 20, 25, 30]
            all_unique_products = set()
            
            for page in pages_to_test:
                params = {'PageSize': 10, 'Page': page}
                
                try:
                    response = self.session.get(products_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('Items', [])
                        total = data.get('@total', 0)
                        
                        print(f"\n📄 PAGE {page}:")
                        print(f"  ✅ Status: Success")
                        print(f"  📊 Total products available: {total}")
                        print(f"  📦 Items on this page: {len(items)}")
                        
                        if items:
                            print(f"  🔍 Products found:")
                            for i, item in enumerate(items):
                                name = item.get('Name', 'No name')
                                price = item.get('CurrentPrice', 'No price')
                                product_id = item.get('Id', 'No ID')
                                category = item.get('Category', 'No category')
                                
                                # Track unique products
                                all_unique_products.add(name)
                                
                                print(f"    {i+1}. {name}")
                                print(f"       Price: {price} | Category: {category}")
                                print(f"       ID: {product_id}")
                        else:
                            print(f"  📭 No items found on page {page}")
                            break  # No more pages
                    else:
                        print(f"\n📄 PAGE {page}: ❌ Error {response.status_code}")
                        if response.status_code == 404:
                            print(f"    (Page {page} doesn't exist)")
                            break
                        
                except Exception as e:
                    print(f"\n📄 PAGE {page}: ⚠️ Exception: {str(e)}")
                
                # Small delay between requests
                time.sleep(0.5)
            
            print(f"\n" + "=" * 60)
            print(f"📊 SUMMARY:")
            print(f"  🎯 Total unique products found: {len(all_unique_products)}")
            print(f"  📄 Pages tested: {len(pages_to_test)}")
            
            if len(all_unique_products) <= 5:
                print(f"  ⚠️  WARNING: Very low diversity! Only {len(all_unique_products)} unique products")
                print(f"  🔍 This suggests API limitations or catalog restrictions")
            else:
                print(f"  ✅ Good diversity found!")
            
            print(f"\n🔍 UNIQUE PRODUCT NAMES FOUND:")
            for i, product_name in enumerate(sorted(all_unique_products), 1):
                print(f"  {i}. {product_name}")
                
        except Exception as e:
            print(f"❌ Debug error: {str(e)}")
    
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
    
    def get_product_catalog_with_max_diversity(self, campaign_id=None, target_products=1000):
        """
        Get maximum diversity of products using pagination and smart sampling
        """
        print(f"📦 Fetching maximum diversity of products from Impact.com...")
        print(f"🎯 Target: {target_products} diverse products")
        
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
            
            # Get products from TheRealReal catalog with PAGINATION
            catalog_id = realreal_catalog.get('Id')
            products_url = f"{self.impact_api_base}/Mediapartners/{self.account_sid}/Catalogs/{catalog_id}/Items"
            
            # First, check total available products
            test_params = {'PageSize': 10, 'Page': 1}
            test_response = self.session.get(products_url, params=test_params)
            
            if test_response.status_code != 200:
                print(f"❌ Error testing products endpoint: {test_response.status_code}")
                return []
            
            test_data = test_response.json()
            total_available = test_data.get('@total', 0)
            print(f"📊 Total products available in catalog: {total_available}")
            
            # Calculate optimal pagination strategy
            page_size = min(100, target_products // 10)  # Reasonable page size
            max_pages = min(50, (target_products // page_size) + 1)  # Don't go crazy with pages
            
            print(f"📄 Strategy: {page_size} products per page, up to {max_pages} pages")
            
            all_items = []
            unique_titles = set()  # Track unique products to avoid duplicates
            
            # Strategy 1: Get products from multiple pages for diversity
            pages_to_fetch = list(range(1, max_pages + 1))
            
            # Strategy 2: Randomize which pages we fetch for even more diversity
            if len(pages_to_fetch) > 10:
                # Sample random pages across the full range
                max_possible_page = total_available // page_size
                if max_possible_page > max_pages:
                    random_pages = random.sample(range(1, min(max_possible_page, 100)), max_pages)
                    pages_to_fetch = sorted(random_pages)
                    print(f"🎲 Using random page sampling: {pages_to_fetch[:10]}...")
            
            for page_num in pages_to_fetch:
                if len(all_items) >= target_products:
                    print(f"🎯 Reached target of {target_products} products!")
                    break
                
                params = {
                    'PageSize': page_size,
                    'Page': page_num
                }
                
                print(f"🔍 Fetching page {page_num} (products {len(all_items)}/{target_products})...")
                
                try:
                    products_response = self.session.get(products_url, params=params, timeout=30)
                    
                    if products_response.status_code == 200:
                        products_data = products_response.json()
                        items = products_data.get('Items', [])
                        
                        if not items:
                            print(f"📭 Page {page_num} is empty, stopping pagination")
                            break
                        
                        # Filter out duplicates
                        new_items = 0
                        for item in items:
                            title = item.get('Name', '')
                            if title and title not in unique_titles:
                                unique_titles.add(title)
                                all_items.append(item)
                                new_items += 1
                        
                        print(f"    ✅ Page {page_num}: {new_items} new unique products")
                        
                        # Add small delay to be nice to the API
                        time.sleep(0.5)
                        
                    else:
                        print(f"    ❌ Error on page {page_num}: {products_response.status_code}")
                        continue
                        
                except Exception as e:
                    print(f"    ⚠️ Error fetching page {page_num}: {str(e)}")
                    continue
            
            print(f"✅ Collected {len(all_items)} unique products from {len(pages_to_fetch)} pages!")
            print(f"📈 Diversity achieved: {len(unique_titles)} unique product titles")
            
            # Final shuffle for even more randomness
            random.shuffle(all_items)
            
            return all_items[:target_products]  # Return up to target amount
                
        except Exception as e:
            print(f"❌ Error fetching products: {str(e)}")
            return []
    
    def parse_impact_product(self, item) -> Dict:
        """
        Convert Impact.com product data to Retrofy format
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

            # FIXED: Validate brand and extract from title if invalid
            validated_brand = self.extract_brand_from_title_or_validate(title, brand)

            # If still no valid brand, try description as fallback
            if validated_brand == "Unknown" or not validated_brand:
                validated_brand = self.extract_brand_from_text(description)

            final_brand = self.clean_text(validated_brand)
            
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
                "brand": final_brand,
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
    
    def extract_brand_from_title_or_validate(self, title, brand):
        """Extract brand from title when API brand is invalid (like '0', '1', etc.)"""
        
        # Invalid brand values that we should ignore
        invalid_brands = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '', 'null', 'undefined', 'None']
        
        # Check if brand is invalid
        if not brand or str(brand).strip() in invalid_brands:
            # Use your existing extract_brand_from_text method
            extracted_brand = self.extract_brand_from_text(title)
            return extracted_brand
        
        return brand
    
    def extract_brand_from_text(self, text: str) -> str:
        """Extract brand from text - prioritize title field"""
        
        # Handle cases where text might be a list
        if isinstance(text, list):
            text = ' '.join(str(item) for item in text)
        elif not isinstance(text, str):
            text = str(text)
        
        if not text or text.strip() == "":
            return "Unknown"
            
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
        
        # Check for exact brand matches first
        for brand in luxury_brands:
            if brand.upper() in text_upper:
                return brand
        
        # If no luxury brand found, try to extract a reasonable brand name
        # Clean the text first
        cleaned_text = text.strip()
        
        # If the title/text is just a brand name (common case), return it
        if len(cleaned_text.split()) <= 3 and not any(char.isdigit() for char in cleaned_text):
            return cleaned_text
        
        # Extract first meaningful word(s) as fallback
        words = cleaned_text.split()
        
        if words:
            # Skip common prefixes and get the actual brand
            first_word = words[0]
            # Don't return single digits or very short strings as brand names
            if len(first_word) > 1 and not first_word.isdigit():
                return first_word
        
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
        text = re.sub(r'[^\w\s\-\(\)\.\,\&]', '', text)
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
    
    def run_real_scraping_session(self, limit=1000):
        """
        Run real scraping session with MAXIMUM DIVERSITY
        """
        print("🚀 Starting REAL Impact.com API scraping session...")
        print("💎 Getting maximum diversity of authentic luxury data from TheRealReal!")
        print(f"🎯 Target: {limit} diverse products")
        
        # Test API connection
        success, campaigns_data = self.test_api_connection()
        if not success:
            print("❌ Cannot connect to Impact.com API")
            return False
        
        # Find TheRealReal campaign (for reference)
        campaign_id = self.get_therealreal_campaign_id()
        
        # Get products using the ENHANCED method with maximum diversity
        raw_products = self.get_product_catalog_with_max_diversity(campaign_id, limit)
        
        if not raw_products:
            print("❌ No products found")
            return False
        
        # Parse products
        products = []
        product_types = {}  # Track diversity
        
        for item in raw_products:
            product = self.parse_impact_product(item)
            if product and product.get('title'):
                products.append(product)
                
                # Track product diversity
                category = product.get('category', 'other')
                product_types[category] = product_types.get(category, 0) + 1
        
        if products:
            print(f"\n📦 Successfully parsed {len(products)} luxury products!")
            
            # Show diversity stats
            print(f"\n📊 Product diversity achieved:")
            for category, count in sorted(product_types.items()):
                print(f"  {category}: {count} products")
            
            # Show samples from different categories
            print("\n🔍 Sample products found:")
            for i, product in enumerate(products[:5]):
                print(f"{i+1}. {product['brand']} - {product['title']} - ${product['price']} ({product['category']})")
            
            # Send to Retrofy API
            success = self.send_to_api(products)
            
            if success:
                print(f"\n🎉 REAL SCRAPING COMPLETE! {len(products)} diverse luxury products added to Retrofy!")
                print("🔥 Your luxury aggregator now has REAL diverse inventory!")
                print(f"🎯 Search for 'tote bag' should now work!")
            else:
                print("\n❌ Failed to add products to database")
        else:
            print("\n❌ No valid products could be parsed")
        
        return len(products) > 0


# RUN DEBUG MODE TO SEE WHAT'S HAPPENING
if __name__ == "__main__":
    scraper = RealImpactScraper()
    
    print("🔍 RUNNING DEBUG MODE TO ANALYZE API RESPONSES")
    print("=" * 80)
    
    # First run debug to see what's actually happening
    scraper.debug_api_responses()
    
    print("\n" + "=" * 80)
    print("🤔 Based on the debug results above:")
    print("   - If you see many unique products: API is working well")
    print("   - If you see only 1-5 products repeated: API access is limited")
    print("   - If you see errors: There might be API issues")
    
    # Optionally run the full scraper after debug
    # print("\n🚀 RUNNING FULL SCRAPER...")
    # scraper.run_real_scraping_session(limit=100)