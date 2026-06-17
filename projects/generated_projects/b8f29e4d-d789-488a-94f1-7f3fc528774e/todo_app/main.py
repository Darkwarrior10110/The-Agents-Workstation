from fastapi import FastAPI
from todo_app.routes import router as todos_router

app = FastAPI(
    title="Todo API",
    description="A simple FastAPI application for managing Todo items.",
    version="1.0.0",
)

@app.get("/", status_code=200, tags=["monitoring"], summary="Root API endpoint")
async def root():
    """
    Root endpoint for the Todo API.
    Returns a simple status message indicating the API is running.
    """
    return {"status": "ok", "message": "Todo API is running!"}

app.include_router(todos_router)
