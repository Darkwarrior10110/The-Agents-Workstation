import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field


# Pydantic Models for Todo items
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, examples=["Buy groceries"])
    description: Optional[str] = Field(None, max_length=500, examples=["Milk, eggs, bread"])
    completed: bool = Field(False, examples=[False])


class TodoCreate(TodoBase):
    """Model for creating a new Todo item."""
    pass


class TodoUpdate(BaseModel):
    """Model for updating an existing Todo item."""
    title: Optional[str] = Field(None, min_length=1, max_length=100, examples=["Finish report"])
    description: Optional[str] = Field(None, max_length=500, examples=["Draft sections A and B"])
    completed: Optional[bool] = Field(None, examples=[True])


class Todo(TodoBase):
    """Full Todo item model with ID and timestamps."""
    id: uuid.UUID = Field(..., examples=[uuid.uuid4()])
    created_at: datetime = Field(..., examples=[datetime.now(timezone.utc)])
    updated_at: datetime = Field(..., examples=[datetime.now(timezone.utc)])


# In-memory storage for Todo items
todos_db: Dict[uuid.UUID, Todo] = {}

# FastAPI Application instance
app = FastAPI(
    title="Todo API",
    description="A simple Todo application with in-memory storage using FastAPI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Root endpoint for basic health check (CRITICAL requirement)
@app.get("/", status_code=status.HTTP_200_OK, tags=["System"], summary="Root endpoint")
async def root():
    """
    Root endpoint for basic health check of the Todo API.
    Returns a simple message indicating the API is running.
    """
    return {"message": "Todo API is running!"}


# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK, tags=["System"], summary="Health check endpoint")
async def health_check():
    """
    Health check endpoint to verify API operational status.
    Returns a status 'ok' if the API is running.
    """
    return {"status": "ok"}


# CRUD Endpoints for Todo items

@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED, tags=["Todos"], summary="Create a new Todo")
async def create_todo(todo_create: TodoCreate):
    """
    **Create a new Todo item.**

    - **title**: The title of the todo (required).
    - **description**: An optional description for the todo.
    - **completed**: Initial status of the todo (default: False).
    """
    now = datetime.now(timezone.utc)
    new_todo = Todo(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        **todo_create.model_dump()  # Pydantic V2 method to convert model to dict
    )
    todos_db[new_todo.id] = new_todo
    return new_todo


@app.get("/todos", response_model=List[Todo], tags=["Todos"], summary="Retrieve all Todos")
async def get_all_todos():
    """
    **Retrieve a list of all Todo items.**
    Returns an empty list if no todos are found.
    """
    return list(todos_db.values())


@app.get("/todos/{todo_id}", response_model=Todo, tags=["Todos"], summary="Retrieve a single Todo by ID")
async def get_todo_by_id(todo_id: uuid.UUID):
    """
    **Retrieve a specific Todo item by its ID.**

    - **todo_id**: The unique identifier of the Todo item (UUID).
    """
    todo = todos_db.get(todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with ID {todo_id} not found"
        )
    return todo


@app.put("/todos/{todo_id}", response_model=Todo, tags=["Todos"], summary="Update an existing Todo")
async def update_todo(todo_id: uuid.UUID, todo_update: TodoUpdate):
    """
    **Update an existing Todo item.**

    - **todo_id**: The unique identifier of the Todo item (UUID).
    - **title**: New title for the todo (optional).
    - **description**: New description for the todo (optional).
    - **completed**: New completion status for the todo (optional).
    """
    existing_todo = todos_db.get(todo_id)
    if not existing_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with ID {todo_id} not found"
        )

    # Convert Pydantic model to dict, excluding fields that were not set in the request
    # This ensures only provided fields update the existing todo.
    update_data = todo_update.model_dump(exclude_unset=True)

    # Apply updates to the existing todo item
    for key, value in update_data.items():
        setattr(existing_todo, key, value)

    existing_todo.updated_at = datetime.now(timezone.utc) # Update timestamp on change
    todos_db[todo_id] = existing_todo  # Store the updated object (re-assignment for clarity)

    return existing_todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Todos"], summary="Delete a Todo")
async def delete_todo(todo_id: uuid.UUID):
    """
    **Delete a Todo item by its ID.**

    - **todo_id**: The unique identifier of the Todo item (UUID).
    """
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with ID {todo_id} not found"
        )
    del todos_db[todo_id]
    # FastAPI automatically handles 204 No Content for functions that return None
    return