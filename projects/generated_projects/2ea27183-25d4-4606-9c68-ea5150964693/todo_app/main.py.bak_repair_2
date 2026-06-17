from fastapi import FastAPI
from app.routes import router

# Create the main FastAPI application instance
app = FastAPI(
    title="Todo API",
    description="A simple FastAPI application for managing Todo items.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include the API router from app.routes
# All routes defined in app/routes.py will be prefixed if a prefix is provided,
# but here we include them directly at the root.
app.include_router(router)


@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint of the API.
    """
    return {"message": "Welcome to the Todo API. Visit /docs for OpenAPI documentation."}
