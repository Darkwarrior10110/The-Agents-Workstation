from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import uuid


# Pydantic Models
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    completed: bool = False


class TodoCreate(TodoBase):
    pass


class TodoUpdate(TodoBase):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    completed: Optional[bool] = None


class TodoInDB(TodoBase):
    id: uuid.UUID
    created_at: datetime

    # Pydantic V2 configuration
    class Config:
        from_attributes = True # Enable compatibility with ORM models


# In-memory database
todos_db: Dict[uuid.UUID, TodoInDB] = {}

app = FastAPI(
    title="Todo API",
    description="A simple in-memory Todo application with FastAPI.",
    version="1.0.0",
)

# CORS Middleware
# Allows requests from the frontend origin (e.g., http://localhost:5173 for Vite React app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust if your frontend runs on a different port/domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """
    Root endpoint for the API.
    """
    return {"message": "Welcome to the Todo API!"}


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify API status.
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/todos/", response_model=TodoInDB, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoCreate):
    """
    Create a new todo item.
    """
    new_id = uuid.uuid4()
    now = datetime.now()
    todo_in_db = TodoInDB(id=new_id, created_at=now, **todo.model_dump())
    todos_db[new_id] = todo_in_db
    return todo_in_db


@app.get("/todos/", response_model=List[TodoInDB])
async def read_todos():
    """
    Retrieve all todo items.
    """
    # Sort todos by creation date for consistent ordering
    sorted_todos = sorted(todos_db.values(), key=lambda todo: todo.created_at)
    return sorted_todos


@app.get("/todos/{todo_id}", response_model=TodoInDB)
async def read_todo(todo_id: uuid.UUID):
    """
    Retrieve a single todo item by its ID.
    """
    todo = todos_db.get(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@app.put("/todos/{todo_id}", response_model=TodoInDB)
async def update_todo(todo_id: uuid.UUID, todo_update: TodoUpdate):
    """
    Update an existing todo item by its ID.
    """
    existing_todo = todos_db.get(todo_id)
    if not existing_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    # Only update fields that are provided in the request body (exclude_unset=True)
    update_data = todo_update.model_dump(exclude_unset=True)
    
    # Update existing_todo attributes using the update_data
    for key, value in update_data.items():
        setattr(existing_todo, key, value)
    
    # Return the updated todo item
    return existing_todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: uuid.UUID):
    """
    Delete a todo item by its ID.
    """
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    del todos_db[todo_id]
    return # 204 No Content response