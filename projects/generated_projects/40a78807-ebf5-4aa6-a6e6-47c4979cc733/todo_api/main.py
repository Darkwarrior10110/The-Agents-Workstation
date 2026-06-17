from fastapi import FastAPI
from app.routes import todos

app = FastAPI(
    title="Todo Manager API",
    description="A simple FastAPI application to manage todo items.",
    version="1.0.0"
)

# Include the todo routes with a /api prefix
app.include_router(todos.router, prefix="/api")

@app.get("/", tags=["Root"], summary="Welcome endpoint")
async def root():
    """
    Welcome message for the Todo Manager API. Provides guidance on how to access the API.
    """
    return {"message": "Welcome to the Todo Manager API! Access the interactive documentation at /docs or the API endpoints under /api/"}
