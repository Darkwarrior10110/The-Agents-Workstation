import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Initialize FastAPI app
app = FastAPI(
    title="Cyberpunk Login API",
    description="FastAPI backend for a cyberpunk-themed login page.",
    version="0.1.0",
)

# --- CORS Configuration (CRITICAL for frontend interaction) ---
# This middleware should be added before any routes that might be accessed by a frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust in production for specific frontend domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# --- Jinja2 Templates Configuration ---
# The 'templates' directory is expected to be a sibling of 'main.py'.
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- Static Files Configuration ---
# The 'static' directory is expected to be a sibling of 'main.py'
# for CSS, JavaScript, and images.
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- Routes ---

# CRITICAL: Root GET / endpoint for health checks
@app.get("/", response_class=HTMLResponse, summary="Root health check endpoint")
async def read_root():
    """
    Root endpoint to verify the server is alive.
    Returns a simple 200 OK status with a basic HTML message.
    This is essential for the HealthValidator.
    """
    return Response(content="<h1>FastAPI Server is running!</h1>", status_code=status.HTTP_200_OK)

@app.get("/login", response_class=HTMLResponse, summary="Serve login page")
async def get_login_page(request: Request, error_message: Optional[str] = None):
    """
    Renders the cyberpunk-themed login page (index.html).
    Displays an error message if one is provided (e.g., after a failed login attempt).
    """
    return templates.TemplateResponse(
        request=request,  # CRITICAL: Pass request as a named argument
        name="index.html",
        context={
            "error_message": error_message,
            "request": request # Keep for compatibility, though `request=request` is preferred
        }
    )

@app.post("/login", summary="Handle login form submission")
async def post_login(
    request: Request,
    username: str = Form(..., description="User's login username"),
    password: str = Form(..., description="User's login password")
):
    """
    Handles POST requests for login form submissions using Form data.
    Performs basic credential validation. If successful, redirects to a dashboard.
    If unsuccessful, re-renders the login page with an error message.
    """
    # Basic, hardcoded validation for demonstration purposes.
    # In a real application, this would involve secure password hashing,
    # database lookups, session management, JWT generation, etc.
    if username == "user" and password == "password":
        # Successful login, redirect to a dashboard page.
        # Using HTTP_303_SEE_OTHER for a POST-redirect-GET pattern.
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    else:
        # Failed login, re-render the login page with an error message.
        # This ensures the browser's URL doesn't change on failure.
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error_message": "Invalid credentials. Please try again.",
                "request": request # Keep for compatibility
            }
        )

@app.get("/dashboard", response_class=HTMLResponse, summary="User dashboard after successful login")
async def dashboard(request: Request):
    """
    A placeholder dashboard page for successfully logged-in users.
    In a real application, this route would be protected by authentication middleware.
    """
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html", # Assuming 'dashboard.html' template exists for post-login view
        context={
            "username": "user",
            "message": "Welcome to the Cyber-Dashboard!",
            "request": request # Keep for compatibility
        }
    )

# Optional: Favicon route to prevent 404 errors from browser requests
@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    """Handles favicon requests to prevent 404s. Returns a 204 No Content response."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
