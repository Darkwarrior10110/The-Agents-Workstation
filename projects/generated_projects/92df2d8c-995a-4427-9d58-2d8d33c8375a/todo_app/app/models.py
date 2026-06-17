import uuid
from typing import Dict
from pydantic import BaseModel, Field

# Pydantic model for a Todo item
# This serves as the 'database model' for our in-memory storage
# Request/Response schemas will be defined in schemas.py, potentially inheriting from this or similar structures.
class Todo(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str = Field(..., min_length=1)
    description: str | None = None
    completed: bool = False

# In-memory database for Todos
# Keys are Todo IDs (UUIDs), values are Todo objects
todos_db: Dict[uuid.UUID, Todo] = {}

# Helper function to generate a unique ID for new todos
# Using UUID for robustness instead of simple integer increment
def generate_todo_id() -> uuid.UUID:
    """Generates a unique UUID for a new Todo item."""
    return uuid.uuid4()

# Example of adding a todo directly to the 'database' (for initial testing/setup if needed)
# Not strictly required for the task, but useful to demonstrate usage
# You would typically create and add todos via API routes
# todo_example = Todo(title="Buy groceries", description="Milk, Bread, Eggs")
# todos_db[todo_example.id] = todo_example
