"""
Response shapes. Field names are camelCase on purpose: they match what the
existing frontend code already reads (product.orderLink, product.brandLink,
brand.page, ...), so the JS edits stay small.
"""
from urllib.parse import quote

from pydantic import BaseModel

from .models import Brand, Product


class BrandOut(BaseModel):
    slug: str
    name: str
    logo: str | None = None
    website: str | None = None
    slogan: str | None = None
    social: dict = {}
    page: str  # "brandpage-template.html?brand=Great%20Legacy"
    adImage: str | None = None
    adTitle: str | None = None
    adSubtitle: str | None = None
    adAlt: str | None = None


class ProductOut(BaseModel):
    id: str
    name: str
    price: int  # whole naira
    priceDisplay: str  # "₦31,500"
    image: str
    brand: str  # brand NAME, same as products.js
    brandSlug: str
    brandLink: str
    orderLink: str | None = None
    isFeatured: bool = False
    featuredImage: str | None = None
    collection: str | None = None
    description: str | None = None


def brand_page_link(brand: Brand) -> str:
    return f"brandpage-template.html?brand={quote(brand.name)}"


def serialize_brand(b: Brand) -> BrandOut:
    return BrandOut(
        slug=b.slug,
        name=b.name,
        logo=b.logo,
        website=b.website,
        slogan=b.slogan,
        social=b.social or {},
        page=brand_page_link(b),
        adImage=b.ad_image,
        adTitle=b.ad_title,
        adSubtitle=b.ad_subtitle,
        adAlt=b.ad_alt,
    )


def serialize_product(p: Product, featured_view: bool = False) -> ProductOut:
    # In the carousel, `image` is the carousel picture (it differs from the
    # grid picture), so main.js can keep reading product.image.
    image = (p.featured_image or p.image) if featured_view else p.image
    return ProductOut(
        id=p.id,
        name=p.name,
        price=p.price,
        priceDisplay=f"\u20a6{p.price:,}",
        image=image,
        brand=p.brand.name,
        brandSlug=p.brand.slug,
        brandLink=brand_page_link(p.brand),
        orderLink=p.order_link,
        isFeatured=p.is_featured,
        featuredImage=p.featured_image,
        collection=p.collection,
        description=p.description,
    )
