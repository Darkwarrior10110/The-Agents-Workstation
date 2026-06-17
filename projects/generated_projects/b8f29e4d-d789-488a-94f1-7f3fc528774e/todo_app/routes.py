from typing import List, Dict
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from todo_app.models import TodoItem, TodoItemCreate, TodoItemUpdate


router = APIRouter(prefix="/api/v1", tags=["todos"])

# In-memory storage for Todo items
# Using a dictionary for faster lookup by ID
todos_db: Dict[UUID, TodoItem] = {}

@router.get("/health", status_code=status.HTTP_200_OK, summary="Health Check", tags=["monitoring"])
async def health_check():
    """
    Checks the health of the API.
    Returns a simple status to indicate if the service is running.
    """
    return {"status": "ok"}

@router.post(
    "/todos",
    response_model=TodoItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Todo item"
)
async def create_todo(
    todo: TodoItemCreate
):
    """
    Creates a new Todo item with a unique ID.

    - **title**: Title of the Todo item (required).
    - **description**: Optional description of the Todo item.
    """
    new_todo = TodoItem(**todo.model_dump())
    todos_db[new_todo.id] = new_todo
    return new_todo

@router.get(
    "/todos",
    response_model=List[TodoItem],
    summary="Retrieve all Todo items"
)
async def get_all_todos():
    """
    Retrieves a list of all Todo items currently stored in memory.
    """
    return list(todos_db.values())

@router.get(
    "/todos/{item_id}",
    response_model=TodoItem,
    summary="Retrieve a single Todo item by ID"
)
async def get_todo_by_id(
    item_id: UUID
):
    """
    Retrieves a single Todo item by its unique ID.

    - **item_id**: The UUID of the Todo item to retrieve.
    """
    todo = todos_db.get(item_id)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item_id} not found"
        )
    return todo

@router.put(
    "/todos/{item_id}",
    response_model=TodoItem,
    summary="Update an existing Todo item"
)
async def update_todo(
    item_id: UUID,
    updated_todo: TodoItemUpdate
):
    """
    Updates an existing Todo item by its unique ID.
    All fields are optional, allowing for partial updates.

    - **item_id**: The UUID of the Todo item to update.
    - **title**: New title of the Todo item (optional).
    - **description**: New description of the Todo item (optional).
    - **completed**: New status of the Todo item (optional).
    """
    existing_todo = todos_db.get(item_id)
    if existing_todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item_id} not found"
        )

    # Update fields only if they are provided in the request body
    # exclude_unset=True ensures that only fields explicitly set in the request body are used for update
    update_data = updated_todo.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing_todo, key, value)
    
    todos_db[item_id] = existing_todo
    return existing_todo

@router.delete(
    "/todos/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Todo item"
)
async def delete_todo(
    item_id: UUID
):
    """
    Deletes a Todo item by its unique ID.

    - **item_id**: The UUID of the Todo item to delete.
    """
    if item_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo item with ID {item_id} not found"
        )
    del todos_db[item_id]
    # For 204 No Content, no response body is returned.
    return
