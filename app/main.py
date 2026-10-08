import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

from .routes import router

load_dotenv()  # so CORS_ORIGINS in .env is visible below

app = FastAPI(title="Beelinx API", version="1.0.0")

origins = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "https://beelinx.github.io,http://127.0.0.1:5500,http://localhost:5500",
    ).split(",")
    if o.strip()
]

# Read-only public API, so GET only. Browsers block the site's fetch() calls
# unless its origin is listed here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cache_reads(request: Request, call_next):
    response = await call_next(request)
    if request.method == "GET" and response.status_code == 200:
        # Catalogue data changes rarely; a minute of caching cuts load
        # (and cold-start pain on Render's free tier).
        response.headers.setdefault("Cache-Control", "public, max-age=60")
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(router)
