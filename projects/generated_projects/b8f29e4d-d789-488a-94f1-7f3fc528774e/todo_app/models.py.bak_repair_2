from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


class TodoItem(BaseModel):
    """Pydantic model representing a single Todo item."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier of the Todo item.")
    title: str = Field(min_length=1, max_length=100, description="Title of the Todo item.")
    description: Optional[str] = Field(default=None, max_length=500, description="Optional description of the Todo item.")
    completed: bool = Field(default=False, description="Status of the Todo item (True if completed, False otherwise).")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "title": "Buy groceries",
                "description": "Milk, eggs, bread, and fruits",
                "completed": False
            }
        }
    )


class TodoItemCreate(BaseModel):
    """Pydantic model for creating a new Todo item."""
    title: str = Field(min_length=1, max_length=100, description="Title of the Todo item.")
    description: Optional[str] = Field(default=None, max_length=500, description="Optional description of the Todo item.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Go for a run",
                "description": "Morning run in the park"
            }
        }
    )


class TodoItemUpdate(BaseModel):
    """Pydantic model for updating an existing Todo item."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=100, description="New title of the Todo item.")
    description: Optional[str] = Field(default=None, max_length=500, description="New optional description of the Todo item.")
    completed: Optional[bool] = Field(default=None, description="New status of the Todo item (True if completed, False otherwise).")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Read a book",
                "completed": True
            }
        }
    )
