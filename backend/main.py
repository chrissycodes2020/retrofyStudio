from fastapi import FastAPI, Query, status
from models.product import Product
from schemas.product import ProductCreate
from database import Base, engine, SessionLocal
from typing import List, Optional
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

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
    brand: Optional[str] = Query(None, description="Filter by brand (e.g., 'Chanel', 'Gucci')"),
    category: Optional[str] = Query(None, description="Filter by category (e.g., 'handbags', 'shoes')"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    color: Optional[str] = Query(None, description="Filter by color"),
    platform_name: Optional[str] = Query(None, description="Filter by platform (e.g., 'TheRealReal', 'Vestiaire')"),
    limit: Optional[int] = Query(100, description="Maximum number of results to return")
):
    """
    Get products with optional search and filter parameters.
    
    Example queries:
    - /products (get all products)
    - /products?brand=Chanel&max_price=2000
    - /products?category=handbags&min_price=500&max_price=1500
    - /products?platform_name=TheRealReal&color=black
    """
    db: Session = SessionLocal()
    try:
        # Start with base query
        query = db.query(Product)
        
        # Apply filters based on query parameters
        if brand:
            query = query.filter(Product.brand.ilike(f"%{brand}%"))
        
        if category:
            query = query.filter(Product.category.ilike(f"%{category}%"))
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        if color:
            query = query.filter(Product.color.ilike(f"%{color}%"))
        
        if platform_name:
            query = query.filter(Product.platform_name.ilike(f"%{platform_name}%"))
        
        # Apply limit and execute query
        products = query.limit(limit).all()
        
        return JSONResponse(content=jsonable_encoder(products))

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()

# NEW: Advanced search endpoint with general text search
# REPLACE your /products/search endpoint in main.py with this improved version:

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
    
    Now supports multi-word searches like "chanel bag" or "black leather"!
    
    Example: /products/search?q=chanel bag&max_price=3000&sort_by=price_asc
    """
    db: Session = SessionLocal()
    try:
        query = db.query(Product)
        
        # IMPROVED: Multi-word search logic
        if q:
            # Split search terms by spaces
            search_terms = q.strip().split()
            
            if search_terms:
                # For each search term, check if it appears in title, brand, OR description
                search_conditions = []
                
                for term in search_terms:
                    term_pattern = f"%{term}%"
                    term_condition = (
                        (Product.title.ilike(term_pattern)) |
                        (Product.brand.ilike(term_pattern)) |
                        (Product.description.ilike(term_pattern))
                    )
                    search_conditions.append(term_condition)
                
                # ALL search terms must be found (but can be in different fields)
                # This means "chanel bag" finds items that have "chanel" somewhere AND "bag" somewhere
                from sqlalchemy import and_
                query = query.filter(and_(*search_conditions))
        
        # Apply specific filters (unchanged)
        if brand:
            query = query.filter(Product.brand.ilike(f"%{brand}%"))
        
        if category:
            query = query.filter(Product.category.ilike(f"%{category}%"))
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        # Apply sorting (unchanged)
        if sort_by == "price_asc":
            query = query.order_by(Product.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Product.price.desc())
        elif sort_by == "brand":
            query = query.order_by(Product.brand.asc())
        else:  # default to id
            query = query.order_by(Product.id.asc())
        
        products = query.limit(limit).all()
        
        return JSONResponse(content=jsonable_encoder(products))

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()

# NEW: Helper endpoint to get unique values for filters
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