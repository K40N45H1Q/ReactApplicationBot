from dotenv import dotenv_values
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, select, distinct, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List
from httpx import AsyncClient
from datetime import datetime
import json

# Load config
config = dotenv_values(".env")
BOT_TOKEN = config["BOT_TOKEN"]
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_API = f"https://api.telegram.org/file/bot{BOT_TOKEN}"
ADMIN_CHAT_ID = int(config.get("ADMIN_CHAT_ID", "0"))

# Database setup
engine = create_async_engine(config["DB_URL"])
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

# Models
class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[int]
    gender: Mapped[str]
    category: Mapped[str]
    image_url: Mapped[str]

class CartItem(Base):
    __tablename__ = "cart"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(default=1)

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    name: Mapped[str]
    phone: Mapped[str]
    address: Mapped[str]
    postcode: Mapped[str]
    city: Mapped[str]
    country: Mapped[str]
    items: Mapped[str]
    total: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=func.now())

# Pydantic Schemas
class ProductIn(BaseModel):
    name: str
    price: int
    gender: str
    category: str
    image_url: str

class ProductOut(ProductIn):
    id: int
    class Config:
        from_attributes = True

class CartProductOut(BaseModel):
    id: int
    name: str
    price: int
    gender: str
    category: str
    image_url: str
    quantity: int

    class Config:
        orm_mode = True

class OrderIn(BaseModel):
    user_id: int
    name: str
    phone: str
    address: str
    postcode: str
    city: str
    country: str
    items: List[CartProductOut]
    total: int

# FastAPI setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# Telegram admin message sender
async def send_order_to_admin(order: OrderIn):
    if ADMIN_CHAT_ID == 0:
        return
    async with AsyncClient() as client:
        text_items = "\n".join(
            [f"- {item.name} x{item.quantity} = €{item.price * item.quantity}" for item in order.items]
        )
        text = (
            f"New order!\n"
            f"Name: {order.name}\n"
            f"Phone: {order.phone}\n"
            f"Country: {order.country}\n"
            f"City: {order.city}\n"
            f"Address: {order.address}\n"
            f"Postal Code: {order.postcode}\n"
            f"Items:\n{text_items}\n"
            f"Total: €{order.total}"
        )
        await client.post(f"{BOT_API}/sendMessage", json={
            "chat_id": ADMIN_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        })

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Authorization successful!"}

@app.post("/add_product/")
async def add_product(product: ProductIn, session: AsyncSession = Depends(get_session)):
    exists = await session.execute(
        select(Product)
        .where(Product.name == product.name)
        .where(Product.category == product.category)
        .where(Product.gender == product.gender)
    )
    if exists.scalars().first():
        raise HTTPException(status_code=400, detail="Product already exists")
    session.add(Product(**product.model_dump()))
    await session.commit()
    return {"message": "Product successfully added"}

@app.get("/get_products/", response_model=List[ProductOut])
async def get_products(session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(Product))).scalars().all()

@app.get("/get_product/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/get_categories/")
async def get_categories(gender: str = "unisex", session: AsyncSession = Depends(get_session)):
    return [row[0] for row in (await session.execute(
        select(distinct(Product.category)).where(Product.gender == gender)
    )).all()]

@app.delete("/delete_product/{product_id}")
async def delete_product(product_id: int, session: AsyncSession = Depends(get_session)):
    product = (await session.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await session.delete(product)
    await session.commit()
    return {"message": "Product successfully deleted"}

@app.delete("/delete_category/")
async def delete_category(category: str, session: AsyncSession = Depends(get_session)):
    products = (await session.execute(select(Product).where(Product.category == category))).scalars().all()
    if not products:
        raise HTTPException(status_code=404, detail="Category not found")
    for product in products:
        await session.delete(product)
    await session.commit()
    return {"message": f"Category '{category}' and all its products deleted"}

@app.get("/get_avatar/{user_id}")
async def get_avatar(user_id: int):
    async with AsyncClient() as client:
        r = await client.get(f"{BOT_API}/getUserProfilePhotos", params={"user_id": user_id, "limit": 1})
        if not (d := r.json()).get("ok") or not d["result"]["total_count"]:
            raise HTTPException(404, "Avatar not found")
        fid = d["result"]["photos"][0][0]["file_id"]
        r = await client.get(f"{BOT_API}/getFile", params={"file_id": fid})
        if not (f := r.json()).get("ok"):
            raise HTTPException(500, "Failed to get file info")
        r = await client.get(f"{FILE_API}/{f['result']['file_path']}")
        if r.status_code != 200:
            raise HTTPException(502, "Failed to download avatar")
        return StreamingResponse(r.aiter_bytes(), media_type="image/jpeg")

# CART FUNCTIONALITY
@app.post("/add_to_cart/")
async def add_to_cart(user_id: int, product_id: int, quantity: int = 1, session: AsyncSession = Depends(get_session)):
    cart_item = (await session.execute(
        select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
    )).scalar_one_or_none()

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        session.add(cart_item)

    await session.commit()
    return {"message": "Item added to cart"}

@app.delete("/del_from_cart/")
async def del_from_cart(user_id: int, product_id: int, quantity: int = 1, session: AsyncSession = Depends(get_session)):
    cart_item = (await session.execute(
        select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
    )).scalar_one_or_none()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    if cart_item.quantity > quantity:
        cart_item.quantity -= quantity
    else:
        await session.delete(cart_item)
    await session.commit()
    return {"message": "Item removed from cart"}

@app.get("/get_cart/", response_model=List[CartProductOut])
async def get_cart(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Product, CartItem.quantity)
        .join(CartItem, Product.id == CartItem.product_id)
        .where(CartItem.user_id == user_id)
    )
    data = []
    for product, quantity in result.all():
        prod_dict = product.__dict__.copy()
        prod_dict['quantity'] = quantity
        data.append(prod_dict)
    return data

@app.post("/create_order/")
async def create_order(order_in: OrderIn, session: AsyncSession = Depends(get_session)):
    order_data = order_in.model_dump()
    order = Order(
        user_id=order_data["user_id"],
        name=order_data["name"],
        phone=order_data["phone"],
        address=order_data["address"],
        postcode=order_data["postcode"],
        city=order_data["city"],
        country=order_data["country"],
        items=json.dumps(order_data["items"]),
        total=order_data["total"]
    )
    session.add(order)
    await session.commit()
    await send_order_to_admin(order_in)
    return {"message": "Order created successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
