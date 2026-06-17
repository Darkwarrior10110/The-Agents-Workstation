import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Todo Pydantic Model
# Base model for shared attributes
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Title of the todo item")
    description: Optional[str] = Field(None, max_length=1000, description="Optional detailed description of the todo item")

# Model for creating a new todo (only title and description are provided by the user)
class TodoCreate(TodoBase):
    pass

# Model for updating an existing todo (all fields are optional for partial updates)
class TodoUpdate(TodoBase):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Optional new title for the todo item")
    description: Optional[str] = Field(None, max_length=1000, description="Optional new description for the todo item")
    completed: Optional[bool] = Field(None, description="Optional status indicating if the todo is completed")

# Full Todo model including generated fields (id, completed, created_at)
class Todo(TodoBase):
    id: uuid.UUID = Field(..., description="Unique identifier of the todo item")
    completed: bool = Field(False, description="Status indicating if the todo is completed")
    created_at: datetime = Field(..., description="Timestamp when the todo item was created")

    class ConfigDict:
        from_attributes = True # Enable Pydantic model to be created from ORM/arbitrary class attributes

# In-memory storage for todos
todos_db: Dict[uuid.UUID, Todo] = {}

# Initialize FastAPI application
app = FastAPI(
    title="Todo API",
    description="A simple Todo application with FastAPI and in-memory storage.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware to allow communication from the frontend
origins = [
    "http://localhost",
    "http://localhost:3000",  # Allow the frontend running on port 3000
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all standard HTTP methods
    allow_headers=["*"],  # Allow all headers in the request
)

# Root endpoint (CRITICAL for HealthValidator and basic access check)
@app.get("/", status_code=status.HTTP_200_OK, summary="Root endpoint")
async def root():
    """Returns a simple message indicating the API is running."""
    return {"message": "Todo API is running"}

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK, summary="Health check endpoint")
async def health_check():
    """Checks the health of the API."""
    return {"status": "ok", "message": "API is healthy"}

# CRUD Operations for Todos

@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED, summary="Create a new Todo")
async def create_todo(todo: TodoCreate):
    """Creates a new todo item in the database."""
    new_id = uuid.uuid4()
    now = datetime.now()
    new_todo = Todo(
        id=new_id,
        title=todo.title,
        description=todo.description,
        completed=False,
        created_at=now,
    )
    todos_db[new_id] = new_todo
    return new_todo

@app.get("/todos", response_model=List[Todo], summary="Get all Todos")
async def get_all_todos():
    """Retrieves a list of all todo items, sorted by creation date."""
    # Sort todos by creation date for consistent ordering
    sorted_todos = sorted(todos_db.values(), key=lambda todo: todo.created_at)
    return sorted_todos

@app.get("/todos/{todo_id}", response_model=Todo, summary="Get a single Todo by ID")
async def get_todo_by_id(todo_id: uuid.UUID):
    """Retrieves a single todo item by its unique ID."""
    todo = todos_db.get(todo_id)
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo

@app.put("/todos/{todo_id}", response_model=Todo, summary="Update an existing Todo")
async def update_todo(todo_id: uuid.UUID, todo_update: TodoUpdate):
    """Updates an existing todo item by its ID. Supports partial updates."""
    existing_todo = todos_db.get(todo_id)
    if existing_todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # Get only the fields that were provided in the request body for update
    update_data = todo_update.model_dump(exclude_unset=True)

    # Apply updates to the existing todo item, creating a new validated instance
    updated_todo = existing_todo.model_copy(update=update_data)
    
    todos_db[todo_id] = updated_todo
    
    return updated_todo

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a Todo")
async def delete_todo(todo_id: uuid.UUID):
    """Deletes a todo item by its unique ID."""
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    del todos_db[todo_id]
    return # No content returned for 204 status