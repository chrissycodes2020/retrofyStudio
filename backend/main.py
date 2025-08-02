from fastapi import FastAPI, Query, status
from models.product import Product
from schemas.product import ProductCreate
from database import Base, engine, SessionLocal
from typing import List, Optional
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import unicodedata


def remove_accents(text: str) -> str:
    """
    Remove accents from text to make searches more user-friendly
    'Hermès' becomes 'Hermes'
    """
    if not text:
        return ""
    
    # Normalize unicode characters and remove accents
    normalized = unicodedata.normalize('NFD', text)
    without_accents = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
    return without_accents


def smart_category_match(search_term: str, product) -> bool:
    """
    COMPREHENSIVE smart category matching based on organizational chart
    Matches the exact structure from the visual reference
    """
    if not search_term:
        return True
    
    search_lower = search_term.lower().strip()
    
    # Create searchable text from all product fields
    search_text = f"{product.title or ''} {product.description or ''} {product.category or ''}".lower()
    
    # BAG CATEGORY (based on visual reference)
    bag_terms = {
        'bags': ['bag', 'bags', 'handbag', 'handbags', 'purse', 'purses', 'backpack', 'backpacks', 
                'clutch', 'clutches', 'crossbody', 'cross body', 'shoulder bag', 'shoulder bags',
                'luggage', 'travel', 'tote', 'totes'],
        'bag': ['bag', 'bags', 'handbag', 'handbags', 'purse', 'purses'],
        'handbags': ['handbag', 'handbags', 'bag', 'bags', 'purse', 'purses'],
        'handbag': ['handbag', 'handbags', 'bag', 'bags'],
        'backpacks': ['backpack', 'backpacks', 'rucksack', 'daypack'],
        'backpack': ['backpack', 'backpacks'],
        'clutches': ['clutch', 'clutches', 'evening bag', 'evening clutch', 'minaudiere'],
        'clutch': ['clutch', 'clutches', 'evening bag'],
        'crossbody': ['crossbody', 'cross body', 'messenger bag', 'sling bag'],
        'luggage': ['luggage', 'travel bag', 'travel', 'suitcase', 'duffle', 'carry on'],
        'shoulder': ['shoulder bag', 'shoulder bags', 'hobo', 'hobos'],
        'tote': ['tote', 'totes', 'tote bag', 'large bag'],
        'totes': ['tote', 'totes', 'tote bag']
    }
    
    # CLOTHING CATEGORY (based on visual reference)
    clothing_terms = {
        'clothing': ['clothing', 'clothes', 'blouse', 'blouses', 'coat', 'coats', 'denim', 'jeans',
                    'dress', 'dresses', 'jacket', 'jackets', 'knitwear', 'knit', 'pants', 'trousers',
                    'shorts', 'skirt', 'skirts', 'sweater', 'sweaters', 'top', 'tops', 'shirt', 'shirts'],
        'clothes': ['clothing', 'clothes', 'apparel'],
        'blouses': ['blouse', 'blouses', 'shirt', 'shirts', 'top', 'tops'],
        'blouse': ['blouse', 'blouses', 'shirt'],
        'coats': ['coat', 'coats', 'jacket', 'jackets', 'outerwear', 'trench', 'parka'],
        'coat': ['coat', 'coats', 'jacket', 'outerwear'],
        'denim': ['denim', 'jeans', 'jean jacket', 'denim jacket'],
        'jeans': ['jeans', 'denim', 'pants', 'trousers'],
        'dresses': ['dress', 'dresses', 'gown', 'gowns', 'frock'],
        'dress': ['dress', 'dresses', 'gown'],
        'jackets': ['jacket', 'jackets', 'blazer', 'blazers', 'cardigan', 'cardigans'],
        'jacket': ['jacket', 'jackets', 'blazer'],
        'knitwear': ['knitwear', 'knit', 'sweater', 'sweaters', 'cardigan', 'pullover'],
        'knit': ['knit', 'knitwear', 'sweater'],
        'pants': ['pants', 'trousers', 'slacks', 'leggings'],
        'trousers': ['trousers', 'pants', 'slacks'],
        'shorts': ['shorts', 'short pants', 'bermuda'],
        'skirts': ['skirt', 'skirts', 'mini skirt', 'midi skirt', 'maxi skirt'],
        'skirt': ['skirt', 'skirts'],
        'sweaters': ['sweater', 'sweaters', 'jumper', 'pullover', 'cardigan'],
        'sweater': ['sweater', 'sweaters', 'jumper'],
        'tops': ['top', 'tops', 'blouse', 'blouses', 'shirt', 'shirts', 'tee', 'tank'],
        'top': ['top', 'tops', 'blouse', 'shirt']
    }
    
    # SHOE CATEGORY (based on visual reference)  
    shoe_terms = {
        'shoes': ['shoe', 'shoes', 'boot', 'boots', 'espadrille', 'espadrilles', 'flat', 'flats',
                 'loafer', 'loafers', 'mule', 'mules', 'pump', 'pumps', 'sandal', 'sandals',
                 'sneaker', 'sneakers', 'wedge', 'wedges', 'heel', 'heels'],
        'shoe': ['shoe', 'shoes'],
        'boots': ['boot', 'boots', 'ankle boot', 'knee boot', 'thigh boot', 'combat boot', 
                 'chelsea boot', 'riding boot', 'cowboy boot'],
        'boot': ['boot', 'boots'],
        'espadrilles': ['espadrille', 'espadrilles', 'rope sole', 'canvas shoe'],
        'espadrille': ['espadrille', 'espadrilles'],
        'flats': ['flat', 'flats', 'ballet flat', 'ballet flats', 'ballerina'],
        'flat': ['flat', 'flats', 'ballet flat'],
        'loafers': ['loafer', 'loafers', 'moccasin', 'moccasins', 'slip on'],
        'loafer': ['loafer', 'loafers', 'moccasin'],
        'mules': ['mule', 'mules', 'slide', 'slides', 'clog', 'clogs'],
        'mule': ['mule', 'mules', 'slide'],
        'pumps': ['pump', 'pumps', 'court shoe', 'heel', 'heels', 'high heel'],
        'pump': ['pump', 'pumps', 'heel'],
        'sandals': ['sandal', 'sandals', 'flip flop', 'flip flops', 'thong', 'slide'],
        'sandal': ['sandal', 'sandals'],
        'sneakers': ['sneaker', 'sneakers', 'trainer', 'trainers', 'athletic shoe', 'running shoe', 'tennis shoe'],
        'sneaker': ['sneaker', 'sneakers', 'trainer'],
        'wedges': ['wedge', 'wedges', 'wedge heel', 'platform'],
        'wedge': ['wedge', 'wedges'],
        'heels': ['heel', 'heels', 'pump', 'pumps', 'stiletto', 'stilettos', 'high heel'],
        'heel': ['heel', 'heels', 'pump']
    }
    
    # ACCESSORY CATEGORY (based on visual reference)
    accessory_terms = {
        'accessories': ['accessory', 'accessories', 'belt', 'belts', 'glove', 'gloves', 
                       'hair accessory', 'hair accessories', 'hat', 'hats', 'jewelry', 'jewellery',
                       'scarf', 'scarves', 'sunglasses', 'glasses', 'watch', 'watches', 'wallet', 'wallets'],
        'accessory': ['accessory', 'accessories'],
        'belts': ['belt', 'belts', 'waist belt', 'chain belt', 'leather belt'],
        'belt': ['belt', 'belts'],
        'gloves': ['glove', 'gloves', 'mitten', 'mittens'],
        'glove': ['glove', 'gloves'],
        'hair': ['hair accessory', 'hair accessories', 'headband', 'headbands', 'hair clip', 'barrette'],
        'hats': ['hat', 'hats', 'cap', 'caps', 'beanie', 'beanies', 'fedora', 'beret', 'bucket hat'],
        'hat': ['hat', 'hats', 'cap'],
        'jewelry': ['jewelry', 'jewellery', 'necklace', 'necklaces', 'bracelet', 'bracelets', 
                   'ring', 'rings', 'earring', 'earrings', 'pendant', 'pendants', 'chain', 'chains',
                   'brooch', 'brooches', 'pin', 'pins', 'cufflink', 'cufflinks'],
        'jewellery': ['jewelry', 'jewellery'],
        'necklace': ['necklace', 'necklaces', 'pendant', 'pendants', 'chain', 'chains', 'choker'],
        'necklaces': ['necklace', 'necklaces'],
        'bracelet': ['bracelet', 'bracelets', 'bangle', 'bangles', 'cuff', 'cuffs'],
        'bracelets': ['bracelet', 'bracelets'],
        'ring': ['ring', 'rings', 'band', 'bands'],
        'rings': ['ring', 'rings'],
        'earring': ['earring', 'earrings', 'stud', 'studs', 'hoop', 'hoops', 'drop earring'],
        'earrings': ['earring', 'earrings'],
        'scarves': ['scarf', 'scarves', 'shawl', 'shawls', 'wrap', 'wraps', 'stole', 'pashmina'],
        'scarf': ['scarf', 'scarves', 'shawl'],
        'sunglasses': ['sunglasses', 'glasses', 'eyewear', 'shades', 'sunglass'],
        'glasses': ['glasses', 'sunglasses', 'eyewear'],
        'watches': ['watch', 'watches', 'timepiece', 'chronograph', 'wristwatch'],
        'watch': ['watch', 'watches', 'timepiece'],
        'wallets': ['wallet', 'wallets', 'purse', 'coin purse', 'card holder', 'money clip'],
        'wallet': ['wallet', 'wallets']
    }
    
    # DESIGNER BRANDS (from visual reference)
    designer_terms = {
        'alaia': ['alaia', 'alaïa'],
        'balmain': ['balmain'],
        'bottega': ['bottega veneta', 'bottega'],
        'burberry': ['burberry'],
        'chloe': ['chloe', 'chloé'],
        'dolce': ['dolce gabbana', 'dolce & gabbana', 'dolce'],
        'fendi': ['fendi'],
        'gianvito': ['gianvito rossi'],
        'givenchy': ['givenchy'],
        'gucci': ['gucci'],
        'isabel': ['isabel marant'],
        'lanvin': ['lanvin'],
        'miu': ['miu miu'],
        'oscar': ['oscar de la renta'],
        'prada': ['prada'],
        'saint': ['saint laurent', 'ysl'],
        'valentino': ['valentino']
    }
    
    # Combine all categories
    all_categories = {**bag_terms, **clothing_terms, **shoe_terms, **accessory_terms, **designer_terms}
    
    # Check if search term matches any category
    if search_lower in all_categories:
        terms_to_find = all_categories[search_lower]
        for term in terms_to_find:
            if term in search_text:
                return True
        return False
    
    # If not a recognized category, do regular text matching
    if search_lower in search_text:
        return True
    
    return False


# List of terms that should use smart category matching
SMART_CATEGORY_TERMS = [
    # Bags
    'bags', 'bag', 'handbags', 'handbag', 'backpacks', 'backpack', 'clutches', 'clutch',
    'crossbody', 'luggage', 'shoulder', 'tote', 'totes',
    # Clothing  
    'clothing', 'clothes', 'blouses', 'blouse', 'coats', 'coat', 'denim', 'jeans',
    'dresses', 'dress', 'jackets', 'jacket', 'knitwear', 'knit', 'pants', 'trousers',
    'shorts', 'skirts', 'skirt', 'sweaters', 'sweater', 'tops', 'top',
    # Shoes
    'shoes', 'shoe', 'boots', 'boot', 'espadrilles', 'espadrille', 'flats', 'flat',
    'loafers', 'loafer', 'mules', 'mule', 'pumps', 'pump', 'sandals', 'sandal',
    'sneakers', 'sneaker', 'wedges', 'wedge', 'heels', 'heel',
    # Accessories
    'accessories', 'accessory', 'belts', 'belt', 'gloves', 'glove', 'hair', 'hats', 'hat',
    'jewelry', 'jewellery', 'necklace', 'necklaces', 'bracelet', 'bracelets', 'ring', 'rings',
    'earring', 'earrings', 'scarves', 'scarf', 'sunglasses', 'glasses', 'watches', 'watch',
    'wallets', 'wallet',
    # Designers
    'alaia', 'balmain', 'bottega', 'burberry', 'chloe', 'dolce', 'fendi', 'gianvito',
    'givenchy', 'gucci', 'isabel', 'lanvin', 'miu', 'oscar', 'prada', 'saint', 'valentino'
]


def updated_search_logic(q, product):
    """
    Updated search logic for the /products/search endpoint
    Uses comprehensive smart category matching
    """
    if not q:
        return True
        
    search_terms = q.strip().lower().split()
    
    if len(search_terms) == 1:
        search_term = search_terms[0]
        
        if search_term in SMART_CATEGORY_TERMS:
            # Use smart category matching
            return smart_category_match(search_term, product)
        else:
            # Regular text search for brands, materials, etc.
            searchable_text = ""
            if product.title:
                searchable_text += remove_accents(product.title.lower()) + " "
            if product.brand:
                searchable_text += remove_accents(product.brand.lower()) + " "
            if product.description:
                searchable_text += remove_accents(product.description.lower()) + " "
            
            term_clean = remove_accents(search_term)
            return term_clean in searchable_text
    
    else:
        # Multi-word search logic (brand + category, etc.)
        potential_brand = search_terms[0]
        potential_category = " ".join(search_terms[1:])
        
        # Check if first word is a brand
        brand_clean = remove_accents(potential_brand.lower())
        product_brand = remove_accents(product.brand.lower()) if product.brand else ""
        product_title = remove_accents(product.title.lower()) if product.title else ""
        
        brand_match = (brand_clean in product_brand) or (brand_clean in product_title)
        
        if brand_match:
            # If brand matches, check category using smart matching
            return smart_category_match(potential_category, product)
        else:
            # Fall back to regular "all terms must be found" search
            searchable_text = ""
            if product.title:
                searchable_text += remove_accents(product.title.lower()) + " "
            if product.brand:
                searchable_text += remove_accents(product.brand.lower()) + " "
            if product.description:
                searchable_text += remove_accents(product.description.lower()) + " "
            
            # Check if ALL search terms are found
            for term in search_terms:
                term_clean = remove_accents(term.lower())
                if term_clean not in searchable_text:
                    return False
            return True


app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

# Seed Products Endpoint
@app.post("/seed_products")
def seed_products(products: List[ProductCreate]):
    db = SessionLocal()
    try:
        db_products = [Product(**product.dict()) for product in products]
        db.add_all(db_products)
        db.commit()

        return {"message": "Products seeded successfully!"}

    except Exception as e:
        db.rollback()
        return {"error": str(e)}

    finally:
        db.close()

# Simple root endpoint
@app.get("/")
def read_root():
    return {"message": "Hello from Retrofy Studio!"}

# ENHANCED: GET /products with search parameters
@app.get("/products")
def get_products(
    brand: Optional[str] = Query(None, description="Filter by brand (e.g., 'Chanel', 'Gucci', 'Hermes')"),
    category: Optional[str] = Query(None, description="Smart category filter (e.g., 'hat', 'bag', 'shoe', 'dress', 'handbags', 'shoes')"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    color: Optional[str] = Query(None, description="Filter by color"),
    platform_name: Optional[str] = Query(None, description="Filter by platform (e.g., 'TheRealReal', 'Vestiaire')"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return")
):
    """
    Get products with optional search and filter parameters.
    
    Smart features:
    - Smart category search: 'hat' finds all hats regardless of backend category
    - Smart brand search: searches both brand field AND title field  
    - Accent-insensitive: 'Hermes' finds 'Hermès' items
    - Case insensitive searches
    """
    db: Session = SessionLocal()
    try:
        # Get all products and filter in Python for reliability
        all_products = db.query(Product).all()
        filtered_products = []
        
        for product in all_products:
            # Apply brand filter (searches both brand and title fields)
            if brand:
                brand_clean = remove_accents(brand.lower())
                
                # Check brand field
                product_brand = remove_accents(product.brand.lower()) if product.brand else ""
                brand_in_brand_field = brand_clean in product_brand
                
                # Check title field (where actual brand names are)
                product_title = remove_accents(product.title.lower()) if product.title else ""
                brand_in_title_field = brand_clean in product_title
                
                # If brand not found in either field, skip this product
                if not brand_in_brand_field and not brand_in_title_field:
                    continue
            
            # Smart category filtering
            if category:
                if not smart_category_match(category, product):
                    continue
                
            # Apply other filters
            if min_price is not None and product.price < min_price:
                continue
            if max_price is not None and product.price > max_price:
                continue
            if color and color.lower() not in (product.color or "").lower():
                continue
            if platform_name and platform_name.lower() not in (product.platform_name or "").lower():
                continue
            
            filtered_products.append(product)
        
        # Apply limit
        products = filtered_products[:limit]
        
        return JSONResponse(content=jsonable_encoder(products))

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()

# ENHANCED: Advanced search endpoint with comprehensive smart matching
@app.get("/products/search")
def search_products(
    q: Optional[str] = Query(None, description="General search query (searches title, brand, description)"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    category: Optional[str] = Query(None, description="Smart category filter (e.g., 'hat', 'bag', 'shoe', 'dress')"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    sort_by: Optional[str] = Query("id", description="Sort by: 'price_asc', 'price_desc', 'brand', 'id'"),
    limit: Optional[int] = Query(50, description="Maximum results")
):
    """
    Advanced search with comprehensive smart category matching and sorting options.
    
    Smart features:
    - General search: 'birkin bag', 'chanel handbag', 'shoes', 'bags'
    - Smart category: matches ALL category types from organizational chart
    - Smart brand search: works across brand and title fields
    - Accent insensitive: 'hermes' finds 'Hermès'
    - Case insensitive searches
    - Multi-word searches: 'gucci shoes', 'saint laurent bags'
    """
    db: Session = SessionLocal()
    try:
        # Get all products first, then filter in Python for reliability
        all_products = db.query(Product).all()
        filtered_products = []
        
        for product in all_products:
            # Check general search query with smart logic
            if q:
                if not updated_search_logic(q, product):
                    continue
            
            # Apply brand filter (searches both brand and title fields)
            if brand:
                brand_clean = remove_accents(brand.lower())
                
                # Check brand field
                product_brand = remove_accents(product.brand.lower()) if product.brand else ""
                brand_in_brand_field = brand_clean in product_brand
                
                # Check title field (where actual brand names are)
                product_title = remove_accents(product.title.lower()) if product.title else ""
                brand_in_title_field = brand_clean in product_title
                
                # If brand not found in either field, skip this product
                if not brand_in_brand_field and not brand_in_title_field:
                    continue
            
            # Smart category filtering
            if category:
                if not smart_category_match(category, product):
                    continue
            
            # Apply other filters
            if min_price is not None and product.price < min_price:
                continue
            if max_price is not None and product.price > max_price:
                continue
            
            filtered_products.append(product)
        
        # Apply sorting
        if sort_by == "price_asc":
            filtered_products.sort(key=lambda x: x.price or 0)
        elif sort_by == "price_desc":
            filtered_products.sort(key=lambda x: x.price or 0, reverse=True)
        elif sort_by == "brand":
            filtered_products.sort(key=lambda x: x.brand or "")
        # default is no sorting (order by id)
        
        # Apply limit
        products = filtered_products[:limit]
        
        return JSONResponse(content=jsonable_encoder(products))

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()

# Helper endpoint to get unique values for filters
@app.get("/products/filters")
def get_filter_options():
    """
    Get unique values for filter dropdowns in frontend.
    """
    db: Session = SessionLocal()
    try:
        brands = db.query(Product.brand).distinct().filter(Product.brand.isnot(None)).all()
        categories = db.query(Product.category).distinct().filter(Product.category.isnot(None)).all()
        colors = db.query(Product.color).distinct().filter(Product.color.isnot(None)).all()
        platforms = db.query(Product.platform_name).distinct().filter(Product.platform_name.isnot(None)).all()
        
        # Get price range
        from sqlalchemy import func
        price_stats = db.query(
            func.min(Product.price).label('min_price'),
            func.max(Product.price).label('max_price')
        ).first()
        
        return {
            "brands": [brand[0] for brand in brands if brand[0]],
            "categories": [category[0] for category in categories if category[0]],
            "colors": [color[0] for color in colors if color[0]],
            "platforms": [platform[0] for platform in platforms if platform[0]],
            "price_range": {
                "min": price_stats.min_price if price_stats.min_price else 0,
                "max": price_stats.max_price if price_stats.max_price else 0
            }
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()

# DELETE/products endpoint to clear table via API testing
@app.delete("/products", status_code=status.HTTP_200_OK)
def delete_all_products():
    db = SessionLocal()
    try:
        num_deleted = db.query(Product).delete()
        db.commit()
        return {"message": f"Deleted {num_deleted} products."}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

# GET/products/{product_id} to view one product
@app.get("/products/{product_id}")
def get_product_by_id(product_id: int):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            return product
        else:
            return {"error": f"Product with ID {product_id} not found."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

# DELETE/products/{product_id} to delete one specific product by id
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product is None:
            return {"detail": "Product not found"}, 404

        db.delete(product)
        db.commit()

        return {"message": "Product deleted successfully!"}

    except Exception as e:
        db.rollback()
        return {"error": str(e)}

    finally:
        db.close()