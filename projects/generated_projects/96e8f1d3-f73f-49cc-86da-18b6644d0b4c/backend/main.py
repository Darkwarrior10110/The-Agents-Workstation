from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from starlette.middleware.cors import CORSMiddleware
import os

# Initialize FastAPI application
app = FastAPI()

# Configure CORS middleware for frontend interaction (CRITICAL CORS RULE)
# This allows requests from any origin, which is suitable for development.
# For production, replace "*" with specific frontend origin(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Determine the directory for templates relative to this file
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Root endpoint to serve the login page (CRITICAL: Root GET / endpoint)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, error_message: str | None = None):
    """
    Serves the cyberpunk login page (index.html).
    Optionally displays an error message if passed in the context.
    """
    # CRITICAL: Pass 'request' as a named argument, not within the context dictionary.
    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={
            "error_message": error_message
        }
    )

# POST endpoint to handle login submissions
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Handles login form submissions. Uses Form(...) for form data parsing.
    Authenticates against a hardcoded username/password for demonstration.
    """
    # Basic credential check (replace with actual authentication logic for production)
    if username == "user" and password == "password":
        # Successful login: Redirect to the root page.
        # In a real application, you would typically set a session cookie/token here
        # and redirect to a protected dashboard or resource.
        return RedirectResponse(url="/", status_code=HTTP_302_FOUND)
    else:
        # Failed login: Re-render the login page with an error message.
        error_message = "Invalid username or password. Please try again."
        # CRITICAL: Pass 'request' as a named argument.
        return templates.TemplateResponse(
            name="index.html",
            request=request,
            context={
                "error_message": error_message
            }
        )
