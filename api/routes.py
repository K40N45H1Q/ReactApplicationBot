from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from httpx import AsyncClient
from os import getenv
from dotenv import load_dotenv

from api.database import init_db, session as async_session
from api.schemas import CategoryCreate, CategoryResponse, ProductCreate, ProductResponse
from api.crud import (
    create_category,
    get_categories,
    create_product,
    get_products,
    get_category_by_id,
    get_product_by_id,
)

from api.crud import del_product as delete_product

# === Load ENV ===
load_dotenv()
BOT_TOKEN = getenv("BOT_TOKEN")
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_API = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

# === FastAPI instance ===
app = FastAPI()

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можно ограничить, например: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Dependency for DB session ===
async def get_db() -> AsyncSession:
    async with async_session() as db:
        yield db

# === Init DB on startup ===
@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/")
async def root():
    return {"message": "API launched successfully!"}

# === Telegram Avatar ===
@app.get("/avatar/{user_id}")
async def get_avatar(user_id: int):
    async with AsyncClient() as client:
        photos = await client.get(f"{BOT_API}/getUserProfilePhotos", params={"user_id": user_id, "limit": 1})
        data = photos.json()
        if not data.get("ok") or not data["result"]["total_count"]:
            raise HTTPException(404, "Avatar not found")

        file_id = data["result"]["photos"][0][0]["file_id"]
        file_info = await client.get(f"{BOT_API}/getFile", params={"file_id": file_id})
        file_data = file_info.json()
        if not file_data.get("ok"):
            raise HTTPException(500, "Failed to get file info")

        file_url = f"{FILE_API}/{file_data['result']['file_path']}"
        file_resp = await client.get(file_url)
        if file_resp.status_code != 200:
            raise HTTPException(502, "Failed to download avatar")

        return StreamingResponse(file_resp.aiter_bytes(), media_type="image/jpeg")

# === Category Routes ===
@app.post("/categories/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category_route(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await create_category(db, category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/categories/", response_model=List[CategoryResponse])
async def list_categories_route(db: AsyncSession = Depends(get_db)):
    return await get_categories(db)

@app.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category_route(category_id: int, db: AsyncSession = Depends(get_db)):
    category = await get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(404, "Category not found")
    return category

# === Product Routes ===
@app.post("/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product_route(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    return await create_product(db, product)

@app.get("/products/", response_model=List[ProductResponse])
async def list_products_route(db: AsyncSession = Depends(get_db)):
    return await get_products(db)

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_route(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product

@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_route(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await delete_product(db, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
