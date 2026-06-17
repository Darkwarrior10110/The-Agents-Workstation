import React, { useState, useEffect } from 'react';

// Backend API Base URL
const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for creating a new todo
  const [newTodoTitle, setNewTodoTitle] = useState('');
  const [newTodoDescription, setNewTodoDescription] = useState('');

  // State for editing an existing todo
  const [editingTodoId, setEditingTodoId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [editingDescription, setEditingDescription] = useState('');
  const [editingCompleted, setEditingCompleted] = useState(false);

  // Fetches all todos from the backend API
  const fetchTodos = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/todos/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setTodos(data);
    } catch (err) {
      setError('Failed to fetch todos: ' + err.message);
      console.error('Error fetching todos:', err);
    } finally {
      setLoading(false);
    }
  };

  // Effect hook to fetch todos on component mount
  useEffect(() => {
    fetchTodos();
  }, []);

  // Handles the creation of a new todo
  const handleCreateTodo = async (e) => {
    e.preventDefault();
    if (!newTodoTitle.trim()) {
      alert('Todo title cannot be empty.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/todos/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newTodoTitle,
          description: newTodoDescription || null, // Send null if description is empty
          completed: false,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const createdTodo = await response.json();
      setTodos((prevTodos) => [...prevTodos, createdTodo]);
      setNewTodoTitle(''); // Clear form fields
      setNewTodoDescription('');
    } catch (err) {
      setError('Failed to create todo: ' + err.message);
      console.error('Error creating todo:', err);
    } finally {
      setLoading(false);
    }
  };

  // Sets up the form for editing a todo
  const startEditing = (todo) => {
    setEditingTodoId(todo.id);
    setEditingTitle(todo.title);
    setEditingDescription(todo.description || '');
    setEditingCompleted(todo.completed);
  };

  // Cancels the editing process
  const cancelEditing = () => {
    setEditingTodoId(null);
    setEditingTitle('');
    setEditingDescription('');
    setEditingCompleted(false);
  };

  // Handles the update of an existing todo
  const handleUpdateTodo = async (todoId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/todos/${todoId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: editingTitle,
          description: editingDescription || null,
          completed: editingCompleted,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const updatedTodo = await response.json();
      setTodos((prevTodos) =>
        prevTodos.map((todo) => (todo.id === todoId ? updatedTodo : todo))
      );
      cancelEditing(); // Exit editing mode after successful update
    } catch (err) {
      setError('Failed to update todo: ' + err.message);
      console.error('Error updating todo:', err);
    } finally {
      setLoading(false);
    }
  };

  // Toggles the completion status of a todo
  const handleToggleComplete = async (todoId, currentCompleted) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/todos/${todoId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          completed: !currentCompleted, // Toggle the completed status
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const updatedTodo = await response.json();
      setTodos((prevTodos) =>
        prevTodos.map((todo) => (todo.id === todoId ? updatedTodo : todo))
      );
    } catch (err) {
      setError('Failed to toggle todo completion: ' + err.message);
      console.error('Error toggling todo completion:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handles the deletion of a todo
  const handleDeleteTodo = async (todoId) => {
    if (!window.confirm('Are you sure you want to delete this todo?')) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/todos/${todoId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      setTodos((prevTodos) => prevTodos.filter((todo) => todo.id !== todoId));
    } catch (err) {
      setError('Failed to delete todo: ' + err.message);
      console.error('Error deleting todo:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-extrabold text-gray-900 text-center mb-10">
          Todo Application
        </h1>

        {/* Create Todo Form */}
        <div className="bg-white shadow-lg rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Create New Todo</h2>
          <form onSubmit={handleCreateTodo} className="space-y-4">
            <div>
              <label htmlFor="newTodoTitle" className="block text-sm font-medium text-gray-700">
                Title
              </label>
              <input
                type="text"
                id="newTodoTitle"
                value={newTodoTitle}
                onChange={(e) => setNewTodoTitle(e.target.value)}
                placeholder="Buy groceries..."
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                required
              />
            </div>
            <div>
              <label htmlFor="newTodoDescription" className="block text-sm font-medium text-gray-700">
                Description (Optional)
              </label>
              <textarea
                id="newTodoDescription"
                value={newTodoDescription}
                onChange={(e) => setNewTodoDescription(e.target.value)}
                placeholder="Milk, eggs, bread..."
                rows="3"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              ></textarea>
            </div>
            <button
              type="submit"
              className="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              disabled={loading}
            >
              {loading && !editingTodoId ? 'Adding Todo...' : 'Add Todo'}
            </button>
          </form>
        </div>

        {/* Loading and Error States */}
        {loading && <p className="text-center text-indigo-600 text-lg mb-4">Loading todos...</p>}
        {error && <p className="text-center text-red-600 text-lg mb-4">Error: {error}</p>}

        {/* Todo List */}
        {!loading && !error && todos.length === 0 && (
          <p className="text-center text-gray-500 text-lg">No todos yet. Start by creating one!</p>
        )}

        {!loading && !error && todos.length > 0 && (
          <div className="bg-white shadow-lg rounded-lg p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">My Todos</h2>
            <ul className="divide-y divide-gray-200">
              {todos.map((todo) => (
                <li key={todo.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between">
                  {editingTodoId === todo.id ? (
                    // Edit Form for a specific todo
                    <div className="flex-grow space-y-2">
                      <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        required
                      />
                      <textarea
                        value={editingDescription}
                        onChange={(e) => setEditingDescription(e.target.value)}
                        rows="2"
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      ></textarea>
                      <div className="flex items-center">
                        <input
                          id={`completed-${todo.id}`}
                          type="checkbox"
                          checked={editingCompleted}
                          onChange={(e) => setEditingCompleted(e.target.checked)}
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                        />
                        <label htmlFor={`completed-${todo.id}`} className="ml-2 block text-sm text-gray-900">
                          Completed
                        </label>
                      </div>
                      <div className="flex space-x-2 mt-2">
                        <button
                          onClick={() => handleUpdateTodo(todo.id)}
                          className="flex-1 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                          disabled={loading}
                        >
                          {loading ? 'Saving...' : 'Save'}
                        </button>
                        <button
                          onClick={cancelEditing}
                          className="flex-1 inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                          disabled={loading}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    // Display mode for a todo
                    <>
                      <div className="flex-1 min-w-0 pr-4">
                        <div className="flex items-center">
                          <input
                            id={`todo-${todo.id}`}
                            type="checkbox"
                            checked={todo.completed}
                            onChange={() => handleToggleComplete(todo.id, todo.completed)}
                            className="h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded cursor-pointer"
                            disabled={loading}
                          />
                          <label
                            htmlFor={`todo-${todo.id}`}
                            className={`ml-3 text-lg font-medium ${
                              todo.completed ? 'line-through text-gray-500' : 'text-gray-900'
                            }`}
                          >
                            {todo.title}
                          </label>
                        </div>
                        {todo.description && (
                          <p className={`mt-1 ml-8 text-sm text-gray-600 ${todo.completed ? 'line-through' : ''}`}>
                            {todo.description}
                          </p>
                        )}
                        <p className="mt-1 ml-8 text-xs text-gray-400">
                          Created: {new Date(todo.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="mt-3 sm:mt-0 flex space-x-2">
                        <button
                          onClick={() => startEditing(todo)}
                          className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                          disabled={loading}
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteTodo(todo.id)}
                          className="inline-flex items-center px-3 py-1.5 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
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
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
