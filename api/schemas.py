from typing import Optional
from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    products_count: int = 0

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    gender: str
    price: float
    category_id: int
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int

    class Config:
        orm_mode = True