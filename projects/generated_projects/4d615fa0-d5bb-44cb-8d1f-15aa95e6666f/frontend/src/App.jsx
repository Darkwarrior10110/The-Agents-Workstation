import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000/todos';

function App() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newTodoTitle, setNewTodoTitle] = useState('');
  const [newTodoDescription, setNewTodoDescription] = useState('');
  const [editingTodo, setEditingTodo] = useState(null); // Stores the todo being edited

  // Fetch all todos
  const fetchTodos = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(API_BASE_URL);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setTodos(data);
    } catch (err) {
      setError(`Failed to fetch todos: ${err.message}`);
      console.error('Error fetching todos:', err);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch on component mount
  useEffect(() => {
    fetchTodos();
  }, []);

  // Create a new todo
  const createTodo = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(API_BASE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: newTodoTitle, description: newTodoDescription }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const newTodo = await response.json();
      setTodos((prevTodos) => [...prevTodos, newTodo]);
      setNewTodoTitle('');
      setNewTodoDescription('');
    } catch (err) {
      setError(`Failed to create todo: ${err.message}`);
      console.error('Error creating todo:', err);
    } finally {
      setLoading(false);
    }
  };

  // Update a todo (toggle completed status or edit details)
  const updateTodo = async (id, updatedFields) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedFields),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const updatedTodo = await response.json();
      setTodos((prevTodos) =>
        prevTodos.map((todo) => (todo.id === id ? updatedTodo : todo))
      );
      setEditingTodo(null); // Exit editing mode after update
    } catch (err) {
      setError(`Failed to update todo: ${err.message}`);
      console.error('Error updating todo:', err);
    } finally {
      setLoading(false);
    }
  };

  // Delete a todo
  const deleteTodo = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      // FastAPI returns 204 No Content for successful deletion, so no JSON body is expected.
      setTodos((prevTodos) => prevTodos.filter((todo) => todo.id !== id));
    } catch (err) {
      setError(`Failed to delete todo: ${err.message}`);
      console.error('Error deleting todo:', err);
    }
    finally {
      setLoading(false);
    }
  };

  // Handle toggling completion status
  const toggleComplete = (todo) => {
    updateTodo(todo.id, { completed: !todo.completed });
  };

  // Handle setting a todo for editing
  const startEditing = (todo) => {
    setEditingTodo({ ...todo }); // Create a copy to edit
  };

  // Handle changing edit form fields
  const handleEditChange = (e) => {
    const { name, value, type, checked } = e.target;
    setEditingTodo((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  // Handle submitting edit form
  const submitEdit = (e) => {
    e.preventDefault();
    if (editingTodo) {
      updateTodo(editingTodo.id, {
        title: editingTodo.title,
        description: editingTodo.description,
        completed: editingTodo.completed,
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-3xl mx-auto bg-white p-6 rounded-lg shadow-md">
        <h1 className="text-4xl font-bold text-center text-gray-800 mb-8">Todo App</h1>

        {/* Create Todo Form */}
        <form onSubmit={createTodo} className="mb-8 p-4 bg-gray-50 rounded-lg shadow-inner">
          <h2 className="text-2xl font-semibold text-gray-700 mb-4">Add New Todo</h2>
          <div className="mb-4">
            <input
              type="text"
              className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Todo Title"
              value={newTodoTitle}
              onChange={(e) => setNewTodoTitle(e.target.value)}
              required
            />
          </div>
          <div className="mb-4">
            <textarea
              className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Todo Description (optional)"
              rows="3"
              value={newTodoDescription}
              onChange={(e) => setNewTodoDescription(e.target.value)}
            ></textarea>
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75 disabled:opacity-50"
            disabled={loading || !newTodoTitle.trim()}
          >
            {loading ? 'Adding...' : 'Add Todo'}
          </button>
        </form>

        {/* Loading and Error States */}
        {loading && <p className="text-center text-blue-600 mb-4">Loading todos...</p>}
        {error && (
          <p className="text-center text-red-600 mb-4 p-3 bg-red-100 border border-red-400 rounded-md">
            Error: {error}
          </p>
        )}

        {/* Todos List */}
        <h2 className="text-2xl font-semibold text-gray-700 mb-4">Your Todos</h2>
        {todos.length === 0 && !loading && !error ? (
          <p className="text-center text-gray-500 text-lg">No todos yet. Add one above!</p>
        ) : (
          <ul className="space-y-4">
            {todos.map((todo) => (
              <li
                key={todo.id}
                className={`flex flex-col md:flex-row items-start md:items-center justify-between p-4 border border-gray-200 rounded-lg shadow-sm ${todo.completed ? 'bg-green-50' : 'bg-white'}`}
              >
                {editingTodo && editingTodo.id === todo.id ? (
                  // Edit Form
                  <form onSubmit={submitEdit} className="w-full space-y-3">
                    <input
                      type="text"
                      name="title"
                      className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      value={editingTodo.title}
                      onChange={handleEditChange}
                      required
                    />
                    <textarea
                      name="description"
                      className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      rows="2"
                      value={editingTodo.description || ''}
                      onChange={handleEditChange}
                    ></textarea>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        name="completed"
                        id={`completed-${todo.id}`}
                        checked={editingTodo.completed}
                        onChange={handleEditChange}
                        className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                      />
                      <label htmlFor={`completed-${todo.id}`} className="ml-2 text-gray-700">
                        Completed
                      </label>
                    </div>
                    <div className="flex justify-end space-x-2">
                      <button
                        type="submit"
                        className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-md disabled:opacity-50"
                        disabled={loading}
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingTodo(null)}
                        className="bg-gray-400 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded-md"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                ) : (
                  // Display Mode
                  <>
                    <div className="flex-1 mr-4">
                      <h3
                        className={`text-xl font-semibold ${todo.completed ? 'line-through text-gray-500' : 'text-gray-800'}`}
                      >
                        {todo.title}
                      </h3>
                      {todo.description && (
                        <p
                          className={`text-gray-600 text-sm mt-1 ${todo.completed ? 'line-through' : ''}`}
                        >
                          {todo.description}
                        </p>
                      )}
                      <p className="text-xs text-gray-400 mt-1">
                        Created: {new Date(todo.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2 mt-3 md:mt-0">
                      <button
                        onClick={() => toggleComplete(todo)}
                        className={`py-2 px-4 rounded-md text-sm font-medium ${todo.completed ? 'bg-yellow-500 hover:bg-yellow-600 text-white' : 'bg-green-500 hover:bg-green-600 text-white'}`}
                        disabled={loading}
                      >
                        {todo.completed ? 'Uncomplete' : 'Complete'}
                      </button>
                      <button
                        onClick={() => startEditing(todo)}
                        className="bg-indigo-500 hover:bg-indigo-600 text-white py-2 px-4 rounded-md text-sm font-medium"
                        disabled={loading}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => deleteTodo(todo.id)}
                        className="bg-red-500 hover:bg-red-600 text-white py-2 px-4 rounded-md text-sm font-medium"
                        disabled={loading}
                      >
                        Delete
                      </button>
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default App;
