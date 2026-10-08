from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

# JSONB on Postgres, plain JSON on SQLite.
JsonType = JSON().with_variant(JSONB(), "postgresql")


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    logo: Mapped[str | None] = mapped_column(String(500))
    website: Mapped[str | None] = mapped_column(String(500))
    slogan: Mapped[str | None] = mapped_column(String(200))
    # {"instagram": "...", "tiktok": "...", "twitter": "..."}
    social: Mapped[dict] = mapped_column(JsonType, default=dict)

    # Homepage brand banner (was `brandAds` in products.js)
    ad_image: Mapped[str | None] = mapped_column(String(500))
    ad_title: Mapped[str | None] = mapped_column(String(200))
    ad_subtitle: Mapped[str | None] = mapped_column(String(200))
    ad_alt: Mapped[str | None] = mapped_column(String(200))

    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    products: Mapped[list["Product"]] = relationship(back_populates="brand")


class Product(Base):
    __tablename__ = "products"

    # Slug, e.g. "legacy-jorst". Same role as the keys in products.js.
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    price: Mapped[int] = mapped_column(Integer)  # whole naira, e.g. 31500
    image: Mapped[str] = mapped_column(String(500))
    order_link: Mapped[str | None] = mapped_column(String(1000))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Homepage carousel (was `featuredProducts` in products.js)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    featured_order: Mapped[int | None] = mapped_column(Integer)
    featured_image: Mapped[str | None] = mapped_column(String(500))
    collection: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    brand: Mapped[Brand] = relationship(back_populates="products")
