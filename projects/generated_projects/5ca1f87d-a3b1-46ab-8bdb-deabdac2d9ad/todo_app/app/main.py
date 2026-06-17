from fastapi import FastAPI

from todo_app.app.routes import router as todo_router


app = FastAPI(
    title="Todo Manager API",
    description="A simple FastAPI application for managing Todo items.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include the Todo router with a prefix for API versioning
app.include_router(todo_router, prefix="/api/v1", tags=["Todos"])

# No additional middleware is required for this basic setup.
# If CORS or other middleware were needed, they would be added here,
# e.g., app.add_middleware(CORSMiddleware, ...)
