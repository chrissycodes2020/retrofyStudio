from pydantic import BaseModel

class ProductCreate(BaseModel):
    title: str
    brand: str
    category: str
    color: str
    description: str
    price: float
    image_url: str
    platform_name: str
    product_url: str
