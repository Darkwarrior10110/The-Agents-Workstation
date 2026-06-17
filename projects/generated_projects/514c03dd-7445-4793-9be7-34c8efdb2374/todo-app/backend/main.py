from fastapi import FastAPI, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

# 1. FastAPI App Initialization
app = FastAPI(
    title="Todo App",
    version="0.1.0",
    description="A simple Todo API with in-memory storage."
)

# 2. CORS Middleware
# Allow requests from the frontend application running on http://localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Frontend URL
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

# 3. Pydantic Models (V2)
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, examples=["Buy groceries"])
    description: Optional[str] = Field(None, max_length=500, examples=["Milk, eggs, bread"])
    completed: bool = False

class TodoCreate(TodoBase):
    pass # No additional fields needed for creation

class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100, examples=["Buy organic groceries"])
    description: Optional[str] = Field(None, max_length=500, examples=["Organic milk, cage-free eggs, sourdough bread"])
    completed: Optional[bool] = None

class TodoInDB(TodoBase):
    id: UUID = Field(default_factory=uuid4, examples=["a1b2c3d4-e5f6-7890-1234-567890abcdef"])
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), examples=["2023-10-27T10:00:00Z"])

    model_config = ConfigDict(from_attributes=True) # Enable ORM mode for Pydantic V2

# 4. In-memory Storage
todos_db: Dict[UUID, TodoInDB] = {}

# 5. Root Endpoint (CRITICAL: Required by HealthValidator)
@app.get("/", status_code=status.HTTP_200_OK, summary="Root endpoint")
async def root():
    """
    Root endpoint for the API.
    Returns a welcome message and a 200 OK status.
    """
    return {"message": "Welcome to the Todo API"}

# 6. Health Endpoint
@app.get("/health", status_code=status.HTTP_200_OK, summary="Health check endpoint")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "ok"}

# 7. CRUD Endpoints for Todos

@app.post("/todos/", response_model=TodoInDB, status_code=status.HTTP_201_CREATED, summary="Create a new Todo")
async def create_todo(todo: TodoCreate):
    """
    Creates a new todo item.

    - **title**: The title of the todo (required).
    - **description**: An optional description for the todo.
    - **completed**: The completion status (defaults to false).
    """
    new_todo = TodoInDB(
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
    )
    todos_db[new_todo.id] = new_todo
    return new_todo

@app.get("/todos/", response_model=List[TodoInDB], status_code=status.HTTP_200_OK, summary="Get all Todos")
async def get_all_todos():
    """
    Retrieves a list of all todo items.
    """
    return list(todos_db.values())

@app.get("/todos/{todo_id}", response_model=TodoInDB, status_code=status.HTTP_200_OK, summary="Get a single Todo by ID")
async def get_todo(todo_id: UUID):
    """
    Retrieves a single todo item by its ID.

    - **todo_id**: The UUID of the todo item to retrieve.
    """
    todo = todos_db.get(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo

@app.put("/todos/{todo_id}", response_model=TodoInDB, status_code=status.HTTP_200_OK, summary="Update an existing Todo")
async def update_todo(todo_id: UUID, todo_update: TodoUpdate):
    """
    Updates an existing todo item by its ID.

    - **todo_id**: The UUID of the todo item to update.
    - **todo_update**: The fields to update. Only provided fields will be changed.
    """
    existing_todo = todos_db.get(todo_id)
    if not existing_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    update_data = todo_update.model_dump(exclude_unset=True) # Get only the fields that were actually sent
    
    # Create a new TodoInDB instance by merging existing data with update data
    # This ensures validation and proper handling of defaults if not provided in update_data
    updated_todo_data = existing_todo.model_dump()
    updated_todo_data.update(update_data)
    
    updated_todo = TodoInDB.model_validate(updated_todo_data)
    
    todos_db[todo_id] = updated_todo
    return updated_todo

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a Todo by ID")
async def delete_todo(todo_id: UUID):
    """
    Deletes a todo item by its ID.

    - **todo_id**: The UUID of the todo item to delete.
    """
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    del todos_db[todo_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
