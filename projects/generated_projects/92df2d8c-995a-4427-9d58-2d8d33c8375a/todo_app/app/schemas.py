from pydantic import BaseModel, Field

# Import the base Todo model from models.py to be used as a response schema.
# This makes schemas.py a central place for all API-facing Pydantic models.
from .models import Todo

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

# The 'Todo' model imported from .models will serve as the response model directly.
# No need to define a separate TodoResponse if its structure is identical to Todo.
