from typing import Optional
from pydantic import BaseModel, Field


class TodoBase(BaseModel):
    """Base Pydantic model for Todo item attributes."""
    title: str = Field(..., min_length=1, max_length=100, description="Title of the todo item")
    description: Optional[str] = Field(None, max_length=500, description="Optional description of the todo item")
    completed: bool = Field(False, description="Status indicating if the todo item is completed")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Buy groceries",
                "description": "Milk, eggs, bread, and fruits",
                "completed": False
            }
        }


class TodoCreate(TodoBase):
    """Pydantic model for creating a new Todo item (request body)."""
    # Inherits all fields from TodoBase. No new fields for creation.
    pass


class TodoUpdate(BaseModel):
    """Pydantic model for updating an existing Todo item (request body).
    All fields are optional to allow partial updates.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="New title for the todo item")
    description: Optional[str] = Field(None, max_length=500, description="New optional description for the todo item")
    completed: Optional[bool] = Field(None, description="New completion status for the todo item")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Buy organic groceries",
                "completed": True
            }
        }


class Todo(TodoBase):
    """Pydantic model representing a full Todo item, including its ID (response model)."""
    id: int = Field(..., gt=0, description="Unique identifier of the todo item")

    class Config:
        from_attributes = True  # Enable compatibility with ORM models
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Buy groceries",
                "description": "Milk, eggs, bread, and fruits",
                "completed": False
            }
        }
