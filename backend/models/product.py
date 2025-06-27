from sqlalchemy import Column, Integer, String, Float
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    brand = Column(String, index=True)
    category = Column(String, index=True)
    color = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    image_url = Column(String)
    platform_name = Column(String)
    product_url = Column(String)

