"""
Script to fix brand fields in the database
Updates all products where brand="0" with the correct brand extracted from title
"""

from models.product import Product
from database import SessionLocal
import re

# Your luxury brands list (from the scraper)
LUXURY_BRANDS = [
    'Chanel', 'Louis Vuitton', 'Gucci', 'Hermès', 'Hermes', 'Prada', 'Bottega Veneta',
    'Saint Laurent', 'YSL', 'Balenciaga', 'Celine', 'Dior', 'Fendi', 'Givenchy',
    'Valentino', 'Tom Ford', 'Burberry', 'Cartier', 'Rolex', 'Tiffany',
    'Van Cleef', 'Bulgari', 'Christian Louboutin', 'Jimmy Choo', 'Manolo Blahnik',
    'Bottega', 'Alexander McQueen', 'Versace', 'Armani', 'Dolce', 'Isabel Marant',
    'Jean Paul Gaultier', 'Miu Miu', 'Michael Kors', 'Jason Wu', 'Henry Beguelin',
    'For Love & Lemons', 'Sachin & Babi', 'Momoni', 'Mercedes Castillo',
    'I. Reiss', 'Jil Sander', 'Isaia', 'IWC'
]

def extract_brand_from_title(title: str) -> str:
    """Extract brand from title using the same logic as scraper"""
    if not title or title.strip() == "":
        return "Unknown"
    
    title_upper = title.upper()
    
    # Check for exact brand matches first
    for brand in LUXURY_BRANDS:
        if brand.upper() in title_upper:
            return brand
    
    # If no luxury brand found, use first 1-2 words of title
    words = title.strip().split()
    if len(words) >= 2:
        return ' '.join(words[:2])
    elif len(words) == 1:
        return words[0]
    
    return "Unknown"

def clean_text(text: str) -> str:
    """Clean text function from scraper"""
    if not text:
        return ""
    
    if isinstance(text, list):
        text = ' '.join(str(item) for item in text)
    elif not isinstance(text, str):
        text = str(text)
    
    text = ' '.join(text.split())
    text = re.sub(r'[^\w\s\-\(\)\.\,\&]', '', text)
    return text.strip()

def fix_brands():
    """Fix all products with brand='0' in the database"""
    
    db = SessionLocal()
    
    try:
        # Find all products with brand = "0"
        print("🔍 Finding products with invalid brands...")
        
        products_to_fix = db.query(Product).filter(Product.brand == "0").all()
        
        print(f"📦 Found {len(products_to_fix)} products to fix")
        
        if len(products_to_fix) == 0:
            print("✅ No products need fixing!")
            return
        
        fixed_count = 0
        for product in products_to_fix:
            old_brand = product.brand
            
            # Extract new brand from title
            new_brand = extract_brand_from_title(product.title)
            new_brand = clean_text(new_brand)
            
            # Update the product
            product.brand = new_brand
            
            print(f"  ✅ ID {product.id}: '{old_brand}' → '{new_brand}' (from title: '{product.title[:50]}...')")
            fixed_count += 1
        
        # Commit all changes
        db.commit()
        print(f"\n🎉 Successfully fixed {fixed_count} products!")
        print("✅ All brands updated in database")
        
    except Exception as e:
        print(f"❌ Error fixing brands: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting brand fix process...")
    fix_brands()
    print("✨ Brand fix process complete!")