from typing import List

from fastapi import APIRouter, HTTPException, status

from todo_app.app.models import Todo, TodoCreate, TodoUpdate
from todo_app.app.database import create_todo, get_all_todos, get_todo, update_todo, delete_todo


# Create an APIRouter instance for todo-related endpoints
router = APIRouter()


@router.get("/health", response_model=dict, summary="Check API health status")
async def health_check():
    """Checks if the API is running and responsive."""
    return {"status": "ok"}


@router.post(
    "/todos",
    response_model=Todo,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Todo item",
    description="Creates a new todo item with a title, optional description, and completion status."
)
async def create_todo_item(todo_data: TodoCreate):
    """Create a new Todo item.

    - **title**: Title of the todo item (required, min 1, max 100 characters).
    - **description**: Optional description of the todo item (max 500 characters).
    - **completed**: Completion status (defaults to False).
    """
    new_item = create_todo(todo_data)
    return new_item


@router.get(
    "/todos",
    response_model=List[Todo],
    summary="Retrieve all Todo items",
    description="Returns a list of all todo items currently in the system."
)
async def read_all_todo_items():
    """Retrieve all Todo items."""
    return get_all_todos()


@router.get(
    "/todos/{todo_id}",
    response_model=Todo,
    summary="Retrieve a specific Todo item by ID",
    description="Returns a single todo item matching the provided ID."
)
async def read_todo_item(todo_id: int):
    """Retrieve a specific Todo item by ID.

    - **todo_id**: The unique identifier of the todo item.
    """
    item = get_todo(todo_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo item not found")
    return item


@router.put(
    "/todos/{todo_id}",
    response_model=Todo,
    summary="Update an existing Todo item",
    description="Updates an existing todo item partially or completely using its ID."
)
async def update_todo_item(todo_id: int, todo_data: TodoUpdate):
    """Update an existing Todo item.

    - **todo_id**: The unique identifier of the todo item to update.
    - **todo_data**: The fields to update (title, description, completed are optional).
    """
    updated_item = update_todo(todo_id, todo_data)
    if updated_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo item not found")
    return updated_item


@router.delete(
    "/todos/{todo_id}",
    status_code=status.HTTP_200_OK, # Using 200 OK with a message, as 204 No Content implies no body.
    summary="Delete a Todo item",
    description="Deletes a todo item from the system by its ID."
)
async def delete_todo_item(todo_id: int):
    """Delete a Todo item.

    - **todo_id**: The unique identifier of the todo item to delete.
    """
    if not delete_todo(todo_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo item not found")
    return {"message": "Todo deleted successfully"}
