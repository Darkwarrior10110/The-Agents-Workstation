from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Cyberpunk Login API",
    description="API for a cyberpunk themed login page.",
    version="1.0.0"
)

# --- CORS Configuration ---
# This is crucial for allowing the frontend (served by FastAPI or a separate host)
# to make requests to the backend. Allowing all origins is used for development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific frontend URL in production, e.g., ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["GET", "POST"], # Only GET and POST are needed for this app
    allow_headers=["*"]
)

# --- Static Files Setup ---
# Mount the 'static' directory to serve CSS, JS, images, etc.
# The path will be accessible at /static/filename.css or /static/js/filename.js
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# --- Jinja2Templates Setup ---
# Configure Jinja2 for HTML templating. Templates are in the 'backend/templates' directory.
templates = Jinja2Templates(directory="backend/templates")

# --- Root Endpoint: Serve Login Page ---
@app.get("/", response_class=HTMLResponse, summary="Render the login page")
async def read_root(request: Request):
    """
    Displays the cyberpunk-themed login page. This is the entry point for the frontend.
    """
    return templates.TemplateResponse(request=request, name="index.html", context={})

# --- Login Authentication Endpoint ---
@app.post("/login", response_class=HTMLResponse, summary="Authenticate user login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Handles user login authentication via POST request.
    
    Args:
        request: The FastAPI Request object.
        username (str): The username submitted via the login form.
        password (str): The password submitted via the login form.
        
    Returns:
        HTMLResponse: Renders the login page again with an error message on failure,
                      or redirects to a success page (for now, back to root) on success.
    """
    # Basic authentication logic (for demonstration purposes)
    # In a real application, you would hash passwords, query a database,
    # and implement proper session/token management.
    if username == "testuser" and password == "password123":
        # Successful login, redirect to a dashboard or a success page.
        # For this example, we'll redirect back to the root (which will show the login page again, without error).
        # In a real app, this would be a secure redirect, e.g., to /dashboard
        response = RedirectResponse(url=app.url_path_for("read_root"), status_code=status.HTTP_302_FOUND)
        # Optionally, set a session cookie or token here
        return response
    else:
        # Failed login, re-render the login page with an error message
        error_message = "ACCESS DENIED: Invalid credentials. REPEAT ENTRY."
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error_message": error_message},
            status_code=status.HTTP_401_UNAUTHORIZED # Indicate unauthorized attempt
        )

# --- Health Check Endpoint ---
# CRITICAL: This endpoint is required by the internal HealthValidator.
@app.get("/health", status_code=status.HTTP_200_OK, summary="Health check endpoint")
async def health_check():
    """
    Simple health check endpoint to verify the server is running.
    """
    return {"status": "ok", "message": "FastAPI application is running"}