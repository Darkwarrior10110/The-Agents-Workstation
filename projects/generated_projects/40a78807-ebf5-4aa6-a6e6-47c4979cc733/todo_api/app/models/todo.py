from pydantic import BaseModel
from typing import Optional

class Todo(BaseModel):
    id: Optional[int] = None  # Will be assigned by backend
    title: str
    description: Optional[str] = None
    completed: bool = False
