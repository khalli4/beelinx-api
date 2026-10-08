from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import Brand, Product
from .schemas import BrandOut, ProductOut, serialize_brand, serialize_product

router = APIRouter()


def find_brand(db: Session, key: str) -> Brand | None:
    """Accepts the slug ("great-legacy") OR the name ("Great Legacy"),
    so the existing ?brand=Great%20Legacy links keep working."""
    k = key.strip().lower()
    return db.scalar(
        select(Brand).where(or_(func.lower(Brand.slug) == k, func.lower(Brand.name) == k))
    )


@router.get("/brands", response_model=list[BrandOut])
def list_brands(ads: bool = False, db: Session = Depends(get_db)):
    """All brands (catalogue page). ?ads=true returns only brands that have a
    homepage banner (replaces `brandAds`)."""
    q = select(Brand).order_by(Brand.sort_order, Brand.id)
    if ads:
        q = q.where(Brand.ad_image.is_not(None))
    return [serialize_brand(b) for b in db.scalars(q)]


@router.get("/brands/{brand_key}", response_model=BrandOut)
def get_brand(brand_key: str, db: Session = Depends(get_db)):
    brand = find_brand(db, brand_key)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return serialize_brand(brand)


@router.get("/products", response_model=list[ProductOut])
def list_products(
    brand: str | None = None,
    featured: bool = False,
    db: Session = Depends(get_db),
):
    """
    /products                      -> every product (homepage grid)
    /products?brand=Great%20Legacy -> one brand's products (brand page,
                                      "More by brand" on the product page)
    /products?featured=true        -> the carousel, in carousel order
    """
    q = select(Product).options(joinedload(Product.brand))

    if brand:
        b = find_brand(db, brand)
        if not b:
            return []
        q = q.where(Product.brand_id == b.id)

    if featured:
        q = q.where(Product.is_featured.is_(True)).order_by(
            Product.featured_order, Product.id
        )
    else:
        q = q.order_by(Product.sort_order, Product.id)

    return [serialize_product(p, featured_view=featured) for p in db.scalars(q)]


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.scalar(
        select(Product).options(joinedload(Product.brand)).where(Product.id == product_id)
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(product)
