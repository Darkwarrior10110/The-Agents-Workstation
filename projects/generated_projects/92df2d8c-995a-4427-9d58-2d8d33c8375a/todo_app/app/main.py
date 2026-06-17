from fastapi import FastAPI

from .routes import todo_router, health_router

app = FastAPI(
    title="Todo Application API",
    description="A simple FastAPI application for managing Todo items.",
    version="0.1.0",
)

# Include the health router
app.include_router(health_router)

# Include the todo router
app.include_router(todo_router)


@app.get("/", tags=["Root"], summary="Root endpoint")
async def read_root():
    """
    Provides a welcome message and directs users to API documentation.
    """
    return {"message": "Welcome to the Todo API. Visit /docs for API documentation."}
