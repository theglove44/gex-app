from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import gex

app = FastAPI(
    title="GEX Tool API",
    description="Backend API for Gamma Exposure Analysis Tool",
    version="1.0.0",
)

# CORS Configuration
origins = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(gex.router, prefix="/api/v1/gex", tags=["gex"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "gex-tool-api"}
