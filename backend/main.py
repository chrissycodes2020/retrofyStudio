from fastapi import FastAPI
from models.product import Product
from schemas.product import ProductCreate
from database import Base, engine, SessionLocal
from typing import List

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


# Edit JSON in browser window

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

@app.get("/products")
def get_products():
    db: Session = SessionLocal()
    try:
        products = db.query(Product).all()
        return JSONResponse(content=jsonable_encoder(products))

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()
# DELETE/products endpoint to clear table via API testing

from fastapi import status

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



