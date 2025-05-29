from fastapi import FastAPI, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from pydantic import BaseModel
import os, uvicorn, asyncio

engine = create_async_engine(os.getenv("DB_URL", "sqlite+aiosqlite:///./test.db"))
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    gender: Mapped[str]
    category: Mapped[str]
    price: Mapped[int]
    image_url: Mapped[str]

class ProductCreate(BaseModel):
    name: str
    gender: str
    category: str
    price: int
    image_url: str

class ProductSchema(ProductCreate):
    id: int
    class Config: from_attributes = True

app = FastAPI()

@app.get("/products/", response_model=list[ProductSchema])
async def get_products(category: str | None = None, gender: str | None = None):
    async with async_session() as session:
        return (await session.execute(
            select(Product).where(
                *(f for f in [
                    Product.category == category if category else None,
                    Product.gender == gender if gender else None
                ] if f)
            )
        )).scalars().all()

@app.get("/categories/")
async def get_categories():
    async with async_session() as session:
        return [row[0] for row in (await session.execute(select(Product.category).distinct())).all()]

@app.post("/products/", response_model=ProductSchema)
async def add_product(product: ProductCreate):
    async with async_session() as session:
        new_product = Product(**product.dict()); session.add(new_product)
        await session.commit(); await session.refresh(new_product); return new_product

@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    async with async_session() as session:
        if not (await session.execute(delete(Product).where(Product.id == product_id))).rowcount:
            raise HTTPException(404, "Product not found")
        await session.commit(); return {"detail": "Product deleted"}

@app.delete("/categories/{category}")
async def delete_category(category: str):
    async with async_session() as session:
        if not (await session.execute(delete(Product).where(Product.category == category))).rowcount:
            raise HTTPException(404, "Category not found")
        await session.commit(); return {"detail": "Category deleted"}

async def init_db():
    async with engine.begin() as session:
        await session.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())
    uvicorn.run(app, host="0.0.0.0", port=8000)