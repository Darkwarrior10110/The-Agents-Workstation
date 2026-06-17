from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
import uuid
from datetime import datetime

# --- Pydantic Models --- #

class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    completed: bool = False

class TodoCreate(TodoBase):
    pass

class TodoUpdate(TodoBase):
    # For updates, all fields are optional
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    completed: Optional[bool] = None

class Todo(TodoBase):
    id: uuid.UUID
    created_at: datetime = Field(default_factory=datetime.now)

    class Config: # Pydantic V1 compatibility for ORM_MODE
        from_attributes = True # Pydantic V2 equivalent for orm_mode

# --- In-memory storage --- #
todos_db: Dict[uuid.UUID, Todo] = {}

# --- FastAPI Application --- #
app = FastAPI(
    title="Todo API",
    description="A simple FastAPI application for managing Todo items.",
    version="1.0.0",
)

# --- CORS Middleware Configuration --- #
# Adjust `origins` in a production environment to be more specific
origins = [
    "http://localhost:3000",  # React frontend
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# --- Root Endpoint (Critical: HealthValidator dependency) --- #
@app.get("/", status_code=status.HTTP_200_OK, tags=["System"])
async def root():
    """Root endpoint, returns a welcome message."""
    return {"message": "Hello from Todo API! Use /docs for API documentation."}

# --- Health Check Endpoint --- #
@app.get("/health", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    Returns a simple status indicating the API is operational.
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# --- CRUD Endpoints for Todos --- #
@app.post("/todos/", response_model=Todo, status_code=status.HTTP_201_CREATED, tags=["Todos"])
async def create_todo(todo_create: TodoCreate) -> Todo:
    """
    Create a new todo item.
    """
    new_id = uuid.uuid4()
    # Use model_dump to convert Pydantic model to a dict, then unpack it
    todo = Todo(id=new_id, **todo_create.model_dump())
    todos_db[new_id] = todo
    return todo

@app.get("/todos/", response_model=List[Todo], tags=["Todos"])
async def read_todos() -> List[Todo]:
    """
    Retrieve all todo items.
    """
    return list(todos_db.values())

@app.get("/todos/{todo_id}", response_model=Todo, tags=["Todos"])
async def read_todo(todo_id: uuid.UUID) -> Todo:
    """
    Retrieve a single todo item by its ID.
    """
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with ID {todo_id} not found"
        )
    return todos_db[todo_id]

@app.put("/todos/{todo_id}", response_model=Todo, tags=["Todos"])
async def update_todo(todo_id: uuid.UUID, todo_update: TodoUpdate) -> Todo:
    """
    Update an existing todo item.
    """
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with ID {todo_id} not found"
        )
    
    existing_todo = todos_db[todo_id]
    
    # Use model_dump(exclude_unset=True) to get only the fields explicitly provided in the request body
    update_data = todo_update.model_dump(exclude_unset=True)
    
    # Create a new Todo instance with updated data, preserving id and created_at
    updated_todo = existing_todo.model_copy(update=update_data)
    todos_db[todo_id] = updated_todo
    
    return updated_todo

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Todos"])
async def delete_todo(todo_id: uuid.UUID):
    """
    Delete a todo item by its ID.
    """
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with ID {todo_id} not found"
        )
    del todos_db[todo_id]
    # For 204 No Content, FastAPI will automatically handle the empty response
    return