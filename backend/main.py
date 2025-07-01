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

# ENHANCED: GET /products with search parameters - FIXED VERSION

@app.get("/products")
def get_products(
    brand: Optional[str] = Query(None, description="Filter by brand (e.g., 'Chanel', 'Gucci', 'Hermes')"),
    category: Optional[str] = Query(None, description="Filter by category (e.g., 'handbags', 'shoes')"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    color: Optional[str] = Query(None, description="Filter by color"),
    platform_name: Optional[str] = Query(None, description="Filter by platform (e.g., 'TheRealReal', 'Vestiaire')"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return")
):
    """
    Get products with optional search and filter parameters.
    
    Supports accent-insensitive brand searching:
    - 'Hermes' finds 'Hermès' items
    - 'hermes' finds 'Hermès' items  
    - Case insensitive
    - Searches BOTH brand field AND title field for brand names
    """
    db: Session = SessionLocal()
    try:
        # Get all products and filter in Python for reliability
        all_products = db.query(Product).all()
        filtered_products = []
        
        for product in all_products:
            # IMPROVED: Apply brand filter (searches both brand and title fields)
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
            
            # Apply other filters
            if category and category.lower() not in (product.category or "").lower():
                continue
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

# ENHANCED: Advanced search endpoint with general text search - FIXED VERSION

@app.get("/products/search")
def search_products(
    q: Optional[str] = Query(None, description="General search query (searches title, brand, description)"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    sort_by: Optional[str] = Query("id", description="Sort by: 'price_asc', 'price_desc', 'brand', 'id'"),
    limit: Optional[int] = Query(50, description="Maximum results")
):
    """
    Advanced search with general query and sorting options.
    
    Supports:
    - Single words: 'birkin', 'chanel', 'bag'
    - Multi-word: 'birkin bag', 'chanel handbag'  
    - Case insensitive: 'BIRKIN', 'birkin', 'Birkin'
    - Accent insensitive: 'hermes' finds 'Hermès'
    - Searches brand field AND title field for brand names
    """
    db: Session = SessionLocal()
    try:
        # Get all products first, then filter in Python for reliability
        all_products = db.query(Product).all()
        filtered_products = []
        
        for product in all_products:
            # Check general search query
            if q:
                search_terms = q.strip().lower().split()
                
                # Create searchable text (title + brand + description)
                searchable_text = ""
                if product.title:
                    searchable_text += remove_accents(product.title.lower()) + " "
                if product.brand:
                    searchable_text += remove_accents(product.brand.lower()) + " "
                if product.description:
                    searchable_text += remove_accents(product.description.lower()) + " "
                
                # Check if ALL search terms are found in the searchable text
                all_terms_found = True
                for term in search_terms:
                    term_clean = remove_accents(term.lower())
                    if term_clean not in searchable_text:
                        all_terms_found = False
                        break
                
                if not all_terms_found:
                    continue
            
            # IMPROVED: Apply brand filter (searches both brand and title fields)
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
            
            # Apply other filters
            if category and category.lower() not in (product.category or "").lower():
                continue
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
        price_stats = db.query(
            db.func.min(Product.price).label('min_price'),
            db.func.max(Product.price).label('max_price')
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