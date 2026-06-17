import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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

    class Config:
        # pydantic v2 requires model_dump_json instead of json_encoders for custom types
        # However, for basic types like UUID and datetime, FastAPI/Pydantic handle serialization implicitly to JSON strings.
        # This config is more for older Pydantic or specific custom type handling if needed.
        from_attributes = True # Enable orm_mode / from_attributes for Pydantic V2

# In-memory storage
todos_db: Dict[uuid.UUID, TodoInDB] = {}

app = FastAPI(
    title="FastAPI Todo API",
    description="A simple To-Do application built with FastAPI and in-memory storage.",
    version="1.0.0"
)

# Configure CORS middleware
# Allows frontend running on http://localhost:5173 to access the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust if your frontend runs on a different port/domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", status_code=status.HTTP_200_OK, summary="Root endpoint")
async def root():
    """Root endpoint for basic health check."""
    return {"message": "FastAPI Todo API is running!"}

@app.get("/health", status_code=status.HTTP_200_OK, summary="Health check")
async def health_check():
    """Returns a simple status to indicate the API is healthy."""
    return {"status": "ok", "timestamp": datetime.now()}

@app.post("/todos", response_model=TodoInDB, status_code=status.HTTP_201_CREATED, summary="Create a new Todo")
async def create_todo(todo: TodoCreate):
    """Creates a new Todo item."""
    new_id = uuid.uuid4()
    now = datetime.now()
    todo_in_db = TodoInDB(id=new_id, created_at=now, **todo.model_dump())
    todos_db[new_id] = todo_in_db
    return todo_in_db

@app.get("/todos", response_model=List[TodoInDB], summary="Retrieve all Todos")
async def get_all_todos():
    """Retrieves a list of all Todo items."""
    return list(todos_db.values())

@app.get("/todos/{todo_id}", response_model=TodoInDB, summary="Retrieve a Todo by ID")
async def get_todo_by_id(todo_id: uuid.UUID):
    """Retrieves a single Todo item by its unique ID."""
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todos_db[todo_id]

@app.put("/todos/{todo_id}", response_model=TodoInDB, summary="Update an existing Todo")
async def update_todo(todo_id: uuid.UUID, todo_update: TodoUpdate):
    """Updates an existing Todo item by its unique ID."""
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    existing_todo = todos_db[todo_id]
    update_data = todo_update.model_dump(exclude_unset=True)
    
    # Update fields only if they are provided in the request
    for field, value in update_data.items():
        setattr(existing_todo, field, value)
    
    todos_db[todo_id] = existing_todo # Re-assign to ensure dict update if needed, though objects are mutable
    return existing_todo

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a Todo")
async def delete_todo(todo_id: uuid.UUID):
    """Deletes a Todo item by its unique ID."""
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    del todos_db[todo_id]
    return # 204 No Content response
