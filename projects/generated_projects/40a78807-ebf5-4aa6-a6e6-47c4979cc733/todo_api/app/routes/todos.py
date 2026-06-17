from fastapi import APIRouter, HTTPException, status
from typing import List, Dict
from ..models.todo import Todo

router = APIRouter()

# In-memory database for demonstration purposes
todos_db: Dict[int, Todo] = {}
current_id = 0

@router.post("/todos/", response_model=Todo, status_code=status.HTTP_201_CREATED, summary="Create a new Todo item")
async def create_todo(todo: Todo):
    """
    Create a new Todo item with a title, optional description, and completion status.
    The ID is automatically assigned by the server.
    """
    global current_id
    current_id += 1
    # Ensure a new ID is assigned even if the client sends one
    new_todo = todo.model_copy(update={"id": current_id})
    todos_db[current_id] = new_todo
    return new_todo

@router.get("/todos/", response_model=List[Todo], summary="Retrieve all Todo items")
async def read_todos():
    """
    Retrieve a list of all existing Todo items.
    """
    return list(todos_db.values())

@router.get("/todos/{todo_id}", response_model=Todo, summary="Retrieve a single Todo item by ID")
async def read_todo(todo_id: int):
    """
    Retrieve a single Todo item based on its unique ID.
    Raises 404 if the Todo item is not found.
    """
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todos_db[todo_id]

@router.put("/todos/{todo_id}", response_model=Todo, summary="Update an existing Todo item")
async def update_todo(todo_id: int, todo: Todo):
    """
    Update an existing Todo item identified by its ID.
    The provided Todo object completely replaces the existing one.
    Raises 404 if the Todo item is not found.
    """
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    # Ensure the ID from the path is preserved for the updated item
    updated_todo = todo.model_copy(update={"id": todo_id})
    todos_db[todo_id] = updated_todo
    return updated_todo

@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a Todo item")
async def delete_todo(todo_id: int):
    """
    Delete a Todo item based on its unique ID.
    Returns 204 No Content on successful deletion.
    Raises 404 if the Todo item is not found.
    """
    if todo_id not in todos_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    del todos_db[todo_id]
    return # FastAPI automatically handles 204 response body for None

@router.get("/health", status_code=status.HTTP_200_OK, summary="Health check endpoint")
async def health_check():
    """
    Provides a simple health check to indicate that the API is running.
    """
    return {"status": "ok", "message": "API is healthy"}
