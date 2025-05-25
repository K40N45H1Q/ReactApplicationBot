from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from api.models import Category, Product
from api.schemas import CategoryCreate, ProductCreate
from sqlalchemy.exc import IntegrityError

# === Category ===

async def create_category(db: AsyncSession, category: CategoryCreate):
    new_category = Category(name=category.name)
    db.add(new_category)
    try:
        await db.commit()
        await db.refresh(new_category)
        return new_category
    except IntegrityError:
        await db.rollback()
        raise ValueError("Категория с таким именем уже существует")

async def get_categories(db: AsyncSession):
    stmt = select(Category)
    result = await db.execute(stmt)
    categories = result.scalars().all()

    # Получаем products_count для каждой категории
    for category in categories:
        stmt_count = select(func.count(Product.id)).where(Product.category_id == category.id)
        count_result = await db.execute(stmt_count)
        category.products_count = count_result.scalar_one()

    return categories

async def get_category_by_id(db: AsyncSession, category_id: int):
    result = await db.execute(select(Category).where(Category.id == category_id))
    return result.scalar_one_or_none()

# === Product ===

async def create_product(session_factory, product_data: dict):
    async with session_factory() as session:
        result = await session.execute(
            select(Category).where(Category.name == product_data["category"])
        )
        category = result.scalar_one_or_none()

        if not category:
            category = Category(name=product_data["category"])
            session.add(category)
            await session.flush()

        new_product = Product(
            name=product_data["name"],
            price=product_data["price"],
            gender=product_data["gender"],
            image_url=product_data["photo"],
            category_id=category.id
        )

        session.add(new_product)
        await session.commit()

async def get_products(db: AsyncSession, gender: str = "male"):
    result = await db.execute(select(Product).where(Product.gender == gender))
    return result.scalars().all()

async def get_product_by_id(db: AsyncSession, product_id: int):
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

async def del_product(db: AsyncSession, product_id: int):
    product = await get_product_by_id(db, product_id)
    if product is None:
        return None
    await db.delete(product)
    await db.commit()
    return product
