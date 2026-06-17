from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

# Pydantic Models
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    completed: bool = False

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None

class TodoInDB(TodoBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True # Pydantic V2 equivalent of `orm_mode = True`

# In-memory storage
todos_db: Dict[UUID, TodoInDB] = {}

# FastAPI App setup
app = FastAPI(
    title="Todo API",
    description="A simple Todo application with CRUD operations",
    version="1.0.0",
)

# CORS Middleware setup
# Allow requests from the frontend at http://localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"] , # Allow all methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"]  # Allow all headers
)

# Root endpoint (required for health validation)
@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "Welcome to the Todo API!"}

# Health endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# CRUD Endpoints for Todos

@app.post("/todos/", response_model=TodoInDB, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoCreate):
    todo_id = uuid4()
    now = datetime.now(timezone.utc)
    todo_in_db = TodoInDB(id=todo_id, created_at=now, **todo.model_dump())
    todos_db[todo_id] = todo_in_db
    return todo_in_db

@app.get("/todos/", response_model=List[TodoInDB])
async def read_todos():
    return list(todos_db.values())

@app.get("/todos/{todo_id}", response_model=TodoInDB)
async def read_todo(todo_id: UUID):
    todo = todos_db.get(todo_id)
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo

@app.put("/todos/{todo_id}", response_model=TodoInDB)
async def update_todo(todo_id: UUID, todo_update: TodoUpdate):
    existing_todo = todos_db.get(todo_id)
    if existing_todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    update_data = todo_update.model_dump(exclude_unset=True)
    
    # Update the existing todo using Pydantic's model_validate for efficient merging
    # First, convert existing_todo to a dictionary, then merge updates
    updated_todo_data = existing_todo.model_dump()
    updated_todo_data.update(update_data)

    # Create a new TodoInDB instance from the updated data
    updated_todo = TodoInDB.model_validate(updated_todo_data)
    
    todos_db[todo_id] = updated_todo
    return updated_todo

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: UUID):
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    del todos_db[todo_id]
    return
