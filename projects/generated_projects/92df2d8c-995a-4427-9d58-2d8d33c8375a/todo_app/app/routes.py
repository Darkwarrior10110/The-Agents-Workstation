import uuid
from typing import List, Dict, Union
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Import the Todo model and in-memory database from models.py
# Using relative import as 'app' is expected to be a package
from .models import Todo, todos_db

# Pydantic models for request bodies
# These are defined here because schemas.py is not yet correctly implemented
# and T5 (DEFINE_SCHEMAS) failed. In a complete project with schemas.py,
# these would typically be imported from schemas.py.
class TodoCreate(BaseModel):
    """
    Schema for creating a new Todo item.
    Does not include ID or 'completed' status, which are handled internally.
    """
    title: str = Field(..., min_length=1, description="Title of the todo item")
    description: str | None = Field(None, description="Optional description of the todo item")

class TodoUpdate(BaseModel):
    """
    Schema for updating an existing Todo item.
    All fields are optional, allowing partial updates.
    """
    title: str | None = Field(None, min_length=1, description="New title for the todo item")
    description: str | None = Field(None, description="New optional description for the todo item")
    completed: bool | None = Field(None, description="New completion status for the todo item")

# Initialize API routers
todo_router = APIRouter(prefix="/todos", tags=["Todos"])
health_router = APIRouter(tags=["Health"])

@health_router.get("/health", summary="Health check endpoint")
async def health_check():
    """
    Checks the health of the application.
    Returns a simple status message indicating the application is running.
    """
    return {"status": "ok", "message": "Todo app is running"}

@todo_router.post(
    "/",
    response_model=Todo,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Todo item",
    description="Creates a new Todo item with a title and an optional description. The 'completed' status defaults to false."
)
async def create_todo(todo_data: TodoCreate):
    """
    Creates a new Todo item.

    - **title**: The title of the todo item (required).
    - **description**: An optional description for the todo item.
    """
    new_todo = Todo(title=todo_data.title, description=todo_data.description)
    todos_db[new_todo.id] = new_todo
    return new_todo

@todo_router.get(
    "/",
    response_model=List[Todo],
    summary="Retrieve all Todo items",
    description="Fetches a list of all available Todo items."
)
async def get_all_todos():
    """
    Retrieves a list of all Todo items.
    """
    return list(todos_db.values())

@todo_router.get(
    "/{todo_id}",
    response_model=Todo,
    summary="Retrieve a single Todo item by ID",
    description="Fetches a specific Todo item using its unique identifier."
)
async def get_todo_by_id(todo_id: uuid.UUID):
    """
    Retrieves a single Todo item by its unique ID.

    Args:
        todo_id (uuid.UUID): The unique identifier of the Todo item.

    Raises:
        HTTPException: 404 Not Found if the Todo item does not exist.

    Returns:
        Todo: The requested Todo item.
    """
    todo = todos_db.get(todo_id)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id '{todo_id}' not found"
        )
    return todo

@todo_router.put(
    "/{todo_id}",
    response_model=Todo,
    summary="Update an existing Todo item by ID",
    description="Updates one or more fields of an existing Todo item identified by its ID. Partial updates are supported."
)
async def update_todo(todo_id: uuid.UUID, todo_update: TodoUpdate):
    """
    Updates an existing Todo item.

    Args:
        todo_id (uuid.UUID): The unique identifier of the Todo item to update.
        todo_update (TodoUpdate): The updated fields for the Todo item.

    Raises:
        HTTPException: 404 Not Found if the Todo item does not exist.

    Returns:
        Todo: The updated Todo item.
    """
    existing_todo = todos_db.get(todo_id)
    if existing_todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id '{todo_id}' not found"
        )

    # Convert Pydantic model to a dictionary, excluding unset fields
    update_data = todo_update.model_dump(exclude_unset=True)
    
    # Create a new Todo instance with updated values using model_copy
    # This ensures immutability if Todo objects were immutable, and correctly applies updates
    updated_todo = existing_todo.model_copy(update=update_data)
    
    todos_db[todo_id] = updated_todo
    return updated_todo

@todo_router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Todo item by ID",
    description="Deletes a Todo item from the system using its unique identifier."
)
async def delete_todo(todo_id: uuid.UUID):
    """
    Deletes a Todo item.

    Args:
        todo_id (uuid.UUID): The unique identifier of the Todo item to delete.

    Raises:
        HTTPException: 404 Not Found if the Todo item does not exist.
    """
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id '{todo_id}' not found"
        )
    del todos_db[todo_id]
    # No content to return for 204. FastAPI handles this by not sending a response body.
    return
