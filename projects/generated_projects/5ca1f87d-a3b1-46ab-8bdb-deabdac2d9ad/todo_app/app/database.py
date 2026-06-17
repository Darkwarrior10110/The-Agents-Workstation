from typing import List, Optional

from todo_app.app.models import Todo, TodoCreate, TodoUpdate


# In-memory list to simulate a database
# This list will hold instances of the Pydantic `Todo` model.
_todos_db: List[Todo] = []
_current_id: int = 0


def create_todo(todo_data: TodoCreate) -> Todo:
    """Creates a new Todo item and adds it to the in-memory database."""
    global _current_id
    _current_id += 1
    # Use Todo Pydantic model to validate and instantiate the new item
    # Note: `model_dump` is used to convert Pydantic model to a dict, compatible with kwargs.
    new_todo = Todo(id=_current_id, **todo_data.model_dump())
    _todos_db.append(new_todo)
    return new_todo


def get_all_todos() -> List[Todo]:
    """Retrieves all Todo items from the in-memory database."""
    return list(_todos_db)


def get_todo(todo_id: int) -> Optional[Todo]:
    """Retrieves a single Todo item by its ID."""
    for todo in _todos_db:
        if todo.id == todo_id:
            return todo
    return None


def update_todo(todo_id: int, todo_data: TodoUpdate) -> Optional[Todo]:
    """Updates an existing Todo item identified by its ID with new data."""
    for index, todo in enumerate(_todos_db):
        if todo.id == todo_id:
            # Get non-None fields from todo_data for partial update
            update_data = todo_data.model_dump(exclude_unset=True)
            
            # Create a dictionary of the current todo, update it, and then validate with Todo model
            # This ensures that any validation rules in the Todo model are reapplied.
            current_todo_dict = todo.model_dump()
            current_todo_dict.update(update_data)
            
            updated_todo = Todo.model_validate(current_todo_dict)
            _todos_db[index] = updated_todo
            return updated_todo
    return None


def delete_todo(todo_id: int) -> bool:
    """Deletes a Todo item by its ID."""
    global _todos_db
    initial_len = len(_todos_db)
    _todos_db = [todo for todo in _todos_db if todo.id != todo_id]
    return len(_todos_db) < initial_len


def reset_database():
    """Resets the in-memory database for testing purposes."""
    global _todos_db, _current_id
    _todos_db = []
    _current_id = 0
