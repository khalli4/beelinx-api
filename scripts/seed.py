"""
Loads data/seed_data.json (made by scripts/export_products.js) into the database.

    python -m scripts.seed            # create tables if needed, upsert everything
    python -m scripts.seed --reset    # DROP all tables first, then reload

Safe to run repeatedly: brands and products are matched by slug and updated.
"""
import json
import re
import sys
from pathlib import Path

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Brand, Product

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "seed_data.json"


def slugify(text: str) -> str:
    """"5 \u2605 TEE" -> "5-star-tee", "Great Legacy" -> "great-legacy"."""
    text = text.replace("\u2605", " star ")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse_price(text: str) -> int:
    """"\u20a631,500" -> 31500"""
    return int(re.sub(r"\D", "", text))


def main(reset: bool = False) -> None:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        ads = {a["brand"]: a for a in data["brandAds"]}

        # ---- brands (+ their homepage banner) ----
        brands_by_name: dict[str, Brand] = {}
        for i, (name, b) in enumerate(data["brands"].items()):
            slug = slugify(name)
            brand = db.scalar(select(Brand).where(Brand.slug == slug)) or Brand(slug=slug)
            ad = ads.get(name, {})
            brand.name = b.get("name", name)
            brand.logo = b.get("logo")
            brand.website = b.get("website")
            brand.slogan = b.get("slogan")
            brand.social = b.get("social", {})
            brand.ad_image = ad.get("image")
            brand.ad_title = ad.get("title")
            brand.ad_subtitle = ad.get("subtitle")
            brand.ad_alt = ad.get("alt")
            brand.sort_order = i
            db.add(brand)
            brands_by_name[name] = brand
        db.flush()

        # ---- products ----
        old_key_to_id: dict[str, str] = {}
        for i, (key, p) in enumerate(data["products"].items()):
            pid = slugify(key)
            old_key_to_id[key] = pid
            product = db.get(Product, pid) or Product(id=pid)
            product.brand_id = brands_by_name[p["brand"]].id
            product.name = p["name"]
            product.price = parse_price(p["price"])
            product.image = p["image"]
            product.order_link = p.get("orderLink")
            product.sort_order = i
            product.is_featured = False
            product.featured_order = None
            db.add(product)
        db.flush()

        # ---- carousel: mark featured products and copy carousel-only fields ----
        for i, f in enumerate(data["featuredProducts"]):
            pid = old_key_to_id.get(f["productId"])
            product = db.get(Product, pid) if pid else None
            if product is None:
                print(f"! featured item {f['productId']!r} has no matching product, skipped")
                continue
            product.is_featured = True
            product.featured_order = i
            product.featured_image = f.get("image")
            product.collection = f.get("collection")
            product.description = f.get("description")

            carousel_price = parse_price(f["price"])
            if carousel_price != product.price:
                print(
                    f"! price mismatch for {pid}: carousel says {carousel_price}, "
                    f"products says {product.price} -> using {product.price}"
                )

        db.commit()

        n_brands = db.query(Brand).count()
        n_products = db.query(Product).count()
        n_featured = db.query(Product).filter(Product.is_featured.is_(True)).count()
        print(f"Done: {n_brands} brands, {n_products} products, {n_featured} featured")


if __name__ == "__main__":
    main(reset="--reset" in sys.argv)
