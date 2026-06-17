from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Debug Agent",
    description="A simple FastAPI application acting as a debug agent to report its status."
)

# CRITICAL CORS RULE: Enable CORS for the debug agent
# This allows other applications (e.g., a frontend or other services) to access this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for simplicity in a debug agent
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/", status_code=200, summary="Get Debug Agent Status")
async def read_root() -> dict[str, str]:
    """
    Root endpoint to check the status of the debug agent.

    Returns:
        A dictionary with a status message.
    """
    return {"status": "Debug agent is running"}
