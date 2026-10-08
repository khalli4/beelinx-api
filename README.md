# Beelinx API

Read-only FastAPI + PostgreSQL backend that replaces `js/products.js` on the
Beelinx site. Every page keeps its own HTML; the JS fetches from this API
instead of reading global objects.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m scripts.seed          # creates tables + loads the data (SQLite by default)
uvicorn app.main:app --reload
```

Docs and a try-it-out page: http://127.0.0.1:8000/docs

## Use Supabase / Postgres

Copy `.env.example` to `.env`, set `DATABASE_URL`, run `python -m scripts.seed`
again. The seed is safe to re-run (it upserts). `--reset` drops all tables first.

The tables are created with `create_all` for now. Once the schema starts
changing, generate an Alembic baseline from `app/models.py`.

## Deploy on Render

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Env vars: `DATABASE_URL`, `CORS_ORIGINS` (must include `https://beelinx.github.io`)

Free-tier instances sleep, so the first request after idle can take 30+ seconds.
Show a "Loading..." state on the pages, and point a free uptime pinger at `/health`.

## Endpoints

| Endpoint | Replaces in the frontend | Used by |
|---|---|---|
| `GET /brands` | `brands` object (loop) | `catalogue.html` |
| `GET /brands?ads=true` | `brandAds` | homepage banners in `main.js` |
| `GET /brands/{name or slug}` | `brands[name]` | `brand-page.js`, `more-info.js` |
| `GET /products` | `products` object | `home-products.js` |
| `GET /products?brand={name or slug}` | filtering `products` by brand | `brand-page.js`, "More by brand" in `more-info.js` |
| `GET /products?featured=true` | `featuredProducts` | carousel in `main.js` |
| `GET /products/{id}` | `products[id]` | `more-info.js` |

Brand lookups accept the display name too, so the existing
`?brand=Great%20Legacy` links keep working with no HTML changes.

## Response shape (matches the old objects)

Product: `id, name, price (int), priceDisplay ("₦31,500"), image, brand (name),
brandSlug, brandLink, orderLink, isFeatured, featuredImage, collection, description`

Brand: `slug, name, logo, website, slogan, social {instagram, tiktok, ...}, page,
adImage, adTitle, adSubtitle, adAlt`

Two things to know:

- `price` is an integer now. Where the old code printed `product.price`, print
  `product.priceDisplay`.
- With `?featured=true`, `image` is the carousel picture (falls back to the
  normal one), so the carousel code can keep reading `product.image`.

## Frontend changes (in the website repo, do it on a branch)

Shared helper, e.g. at the top of `main.js` (or a new `js/api.js` loaded first):

```js
const API = "https://YOUR-APP.onrender.com";   // http://127.0.0.1:8000 locally

async function api(path) {
  const res = await fetch(API + path);
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}
```

| File | Change |
|---|---|
| `brand-page.js` | `brand = await api("/brands/" + encodeURIComponent(brandName))`, `brandProducts = await api("/products?brand=" + encodeURIComponent(brandName))`. The loop gets `product.id` directly instead of `[id, product]`. |
| `more-info.js` | `product = await api("/products/" + productId)`, `brand = await api("/brands/" + encodeURIComponent(product.brand))`, related = `/products?brand=...` filtered with `p.id !== productId`. |
| `home-products.js` | `const products = await api("/products")`, then group by `product.brand` as it does now. It uses `id` and `product`, so wrap each item as `{id: p.id, product: p}`. |
| `catalogue.html` (inline script) | loop over `await api("/brands")` instead of `Object.entries(brands)`. |
| `main.js` carousel | `const featuredProducts = await api("/products?featured=true")`, then build the slides and start any autoplay AFTER it resolves. |
| `main.js` brand ads | `const brandAds = await api("/brands?ads=true")`. Each ad is a brand: link is `ad.page`, image `ad.adImage`, title `ad.adTitle`, subtitle `ad.adSubtitle`. |

Then delete the `<script src="products.js">` tags. Wrap each file's logic in an
`async function init() { ... } init();` and add try/catch with a visible error state.

Also switch `innerHTML` templates to `textContent` for names and prices before
anyone other than the site owner can edit the data.

## Updating products

Until admin endpoints exist: edit `products.js`, run
`node scripts/export_products.js path/to/products.js`, then `python -m scripts.seed`.

## Known data issue

`legacy-jorst` is ₦28,000 in the old carousel and ₦29,000 in the product list.
The seed keeps the product-list price and prints a warning. Check the real price.
