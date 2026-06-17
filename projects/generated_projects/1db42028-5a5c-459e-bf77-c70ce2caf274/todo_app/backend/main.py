from fastapi import FastAPI, HTTPException, status, APIRouter
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

# Pydantic Models
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    completed: bool = Field(False, description="Status of the todo item")

class TodoCreate(TodoBase):
    pass

class TodoUpdate(TodoBase):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    completed: Optional[bool] = None

class TodoInDB(TodoBase):
    id: UUID = Field(..., description="Unique identifier of the todo item")
    created_at: datetime = Field(..., description="Timestamp of when the todo was created")

    class Config:
        from_attributes = True # Pydantic V2 equivalent of orm_mode = True

# In-memory database
todos_db: dict[UUID, TodoInDB] = {}

app = FastAPI(
    title="Todo API",
    description="A simple FastAPI application for managing todo items with in-memory storage.",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all ports/origins for local development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, GET, PUT, DELETE)
    allow_headers=["*"],  # Allows all headers
)

# API Router for /todos endpoints
todo_router = APIRouter(prefix="/api/v1/todos", tags=["Todos"])

@app.get("/", status_code=status.HTTP_200_OK, summary="Root health check")
async def root():
    """Basic root endpoint to confirm the API is running."""
    return {"status": "OK", "message": "Todo API is up and running!"}

@app.get("/health", status_code=status.HTTP_200_OK, summary="Detailed health check")
async def health_check():
    """Provides a detailed health status of the application."""
    return {"status": "OK", "timestamp": datetime.now().isoformat()}

@todo_router.post(
    "",
    response_model=TodoInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new todo item"
)
async def create_todo(todo_data: TodoCreate):
    """Create a new todo item with a unique ID and creation timestamp."""
    new_id = uuid4()
    now = datetime.now()
    todo_in_db = TodoInDB(
        id=new_id,
        created_at=now,
        **todo_data.model_dump()
    )
    todos_db[new_id] = todo_in_db
    return todo_in_db

@todo_router.get(
    "",
    response_model=List[TodoInDB],
    status_code=status.HTTP_200_OK,
    summary="Retrieve all todo items"
)
async def get_all_todos():
    """Retrieve a list of all todo items currently stored."""
    return list(todos_db.values())

@todo_router.get(
    "/{todo_id}",
    response_model=TodoInDB,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a single todo item by ID"
)
async def get_todo_by_id(todo_id: UUID):
    """Retrieve a specific todo item using its unique ID."""
    todo = todos_db.get(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo

@todo_router.put(
    "/{todo_id}",
    response_model=TodoInDB,
    status_code=status.HTTP_200_OK,
    summary="Update an existing todo item"
)
async def update_todo(todo_id: UUID, todo_update: TodoUpdate):
    """Update an existing todo item by ID. Only provided fields will be modified."""
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    current_todo_data = todos_db[todo_id].model_dump()
    update_data = todo_update.model_dump(exclude_unset=True)
    
    updated_todo_data = {**current_todo_data, **update_data}
    todos_db[todo_id] = TodoInDB.model_validate(updated_todo_data)
    
    return todos_db[todo_id]

@todo_router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a todo item"
)
async def delete_todo(todo_id: UUID):
    """Delete a todo item from the database using its unique ID."""
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    del todos_db[todo_id]
    return # No content to return for 204

# Include the todo_router in the main app
app.include_router(todo_router)
