from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import cases, health
from app.core.config import settings

app = FastAPI(
    title="Case Whisperer API",
    description="Legal case tracking and management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(cases.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Case Whisperer API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)