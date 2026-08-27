import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.session import engine, Base
from app.api.endpoints import router as api_router

# Initialize database tables
# (Usually we would use Alembic migrations, but for hackathon ease, direct creation is robust and zero-effort)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RazorRecover AI API",
    description="Autonomous payment failure recovery and revenue protection platform",
    version="1.0.0",
    docs_url="/docs"
)

# Set up CORS middleware for frontend communication
# React Vite runs on 5173, NextJS on 3000. Allow all origins for seamless hackathon testing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to RazorRecover AI API. Access /docs for Swagger documentation.",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
