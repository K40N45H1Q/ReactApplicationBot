from api.database import Base
from typing import Optional, List
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy import Column, String, Float, ForeignKey, Integer

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
    gender: Mapped[str] = mapped_column(nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped["Category"] = relationship(back_populates="products")

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)

    products: Mapped[List["Product"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan"
    )