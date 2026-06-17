import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1/todos';

function App() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newTodoTitle, setNewTodoTitle] = useState('');
  const [newTodoDescription, setNewTodoDescription] = useState('');
  const [editingTodo, setEditingTodo] = useState(null);
  
  useEffect(() => {
    fetchTodos();
  }, []);
  
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
      console.error("Error fetching todos:", err);
      setError(`Failed to fetch todos: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newTodoTitle.trim()) {
      setError('Todo title cannot be empty.');
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      let response;
      let method;
      let url;
      let body;
      
      if (editingTodo) {
        method = 'PUT';
        url = `${API_BASE_URL}/${editingTodo.id}`;
        body = JSON.stringify({
          title: newTodoTitle,
          description: newTodoDescription,
          completed: editingTodo.completed, 
        });
      } else {
        method = 'POST';
        url = API_BASE_URL;
        body = JSON.stringify({
          title: newTodoTitle,
          description: newTodoDescription,
        });
      }
      
      response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! status: ${response.status}. Detail: ${errorData.detail || 'Unknown error'}`);
      }
      
      const updatedTodo = await response.json();
      if (editingTodo) {
        setTodos(todos.map((todo) => (todo.id === updatedTodo.id ? updatedTodo : todo)));
      } else {
        setTodos([...todos, updatedTodo]);
      }
      
      setNewTodoTitle('');
      setNewTodoDescription('');
      setEditingTodo(null);
    } catch (err) {
      console.error('Error submitting todo:', err);
      setError(`Failed to ${editingTodo ? 'update' : 'add'} todo: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  const handleEditClick = (todo) => {
    setEditingTodo(todo);
    setNewTodoTitle(todo.title);
    setNewTodoDescription(todo.description || '');
    setError(null);
  };
  
  const handleCancelEdit = () => {
    setEditingTodo(null);
    setNewTodoTitle('');
    setNewTodoDescription('');
    setError(null);
  };
  
  const handleToggleComplete = async (todo) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/${todo.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ completed: !todo.completed }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! status: ${response.status}. Detail: ${errorData.detail || 'Unknown error'}`);
      }
      
      const updatedTodo = await response.json();
      setTodos(todos.map((t) => (t.id === updatedTodo.id ? updatedTodo : t)));
    } catch (err) {
      console.error('Error toggling todo completion:', err);
      setError(`Failed to toggle completion: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  const handleDelete = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/${id}`, {
        method: 'DELETE',
      });
      
      if (response.status === 204) {
        setTodos(todos.filter((todo) => todo.id !== id));
      } else if (!response.ok) {
        let errorDetail = 'Unknown error';
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorDetail;
        } catch (parseError) {
        }
        throw new Error(`HTTP error! status: ${response.status}. Detail: ${errorDetail}`);
      }
    } catch (err) {
      console.error('Error deleting todo:', err);
      setError(`Failed to delete todo: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="container mx-auto p-4 max-w-2xl bg-white dark:bg-gray-800 shadow-lg rounded-lg mt-8">
    <h1 className="text-4xl font-extrabold text-center mb-8 text-blue-600 dark:text-blue-400">
    React-FastAPI Todo App
    </h1>
    
    {error && (
      <div
      className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded relative mb-4"
      role="alert"
      >
      <strong className="font-bold">Error!</strong>
      <span className="block sm:inline ml-2">{error}</span>
      <span className="absolute top-0 bottom-0 right-0 px-4 py-3">
      <svg
      className="fill-current h-6 w-6 text-red-500"
      role="button"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      onClick={() => setError(null)}
      >
      <title>Close</title>
      <path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z" />
      </svg>
      </span>
      </div>
    )}
    
    <form onSubmit={handleSubmit} className="mb-8 p-6 bg-gray-50 dark:bg-gray-700 rounded-lg shadow-md">
    <h2 className="text-2xl font-bold mb-4 text-gray-800 dark:text-gray-200">
    {editingTodo ? 'Edit Todo' : 'Add New Todo'}
    </h2>
    <div className="mb-4">
    <label htmlFor="title" className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2">
    Title:
    </label>
    <input
    type="text"
    id="title"
    className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
    value={newTodoTitle}
    onChange={(e) => setNewTodoTitle(e.target.value)}
    disabled={loading}
    required
    />
    </div>
    <div className="mb-6">
    <label htmlFor="description" className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2">
    Description (Optional):
    </label>
    <textarea
    id="description"
    className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
    value={newTodoDescription}
    onChange={(e) => setNewTodoDescription(e.target.value)}
    disabled={loading}
    rows={3}
    ></textarea>
    </div>
    <div className="flex items-center justify-between">
    <button
    type="submit"
    className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
    disabled={loading}
    >
    {editingTodo ? 'Update Todo' : 'Add Todo'}
    </button>
    {editingTodo && (
      <button
      type="button"
      onClick={handleCancelEdit}
      className={`bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline ml-2 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      disabled={loading}
      >
      Cancel Edit
      </button>
    )}
    </div>
    </form>
    
    <h2 className="text-2xl font-bold mb-4 text-gray-800 dark:text-gray-200">Your Todos</h2>
    
    {loading && (editingTodo === null) && <p className="text-center text-blue-500 dark:text-blue-300">Loading todos...</p>}
    
    {!loading && todos.length === 0 && <p className="text-center text-gray-500 dark:text-gray-400">No todos yet. Add one above!</p>}
    
    <ul className="space-y-4">
    {todos.map((todo) => (
      <li
      key={todo.id}
      className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 bg-gray-100 dark:bg-gray-700 rounded-lg shadow-sm"
      >
      <div className="flex items-center mb-2 sm:mb-0">
      <input
      type="checkbox"
      checked={todo.completed}
      onChange={() => handleToggleComplete(todo)}
      className="form-checkbox h-5 w-5 text-blue-600 dark:text-blue-400 mr-3"
      disabled={loading}
      />
      <div className="flex-1">
      <p
      className={`text-lg font-semibold ${todo.completed ? 'line-through text-gray-500 dark:text-gray-400' : 'text-gray-900 dark:text-gray-100'}`}
      >
      {todo.title}
      </p>
      {todo.description && (
        <p
        className={`text-sm text-gray-600 dark:text-gray-300 ${todo.completed ? 'line-through' : ''}`}
        >
        {todo.description}
        </p>
      )}
      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
      Created: {new Date(todo.created_at).toLocaleString()}
      </p>
      </div>
      </div>
      <div className="flex space-x-2 mt-2 sm:mt-0">
      <button
      onClick={() => handleEditClick(todo)}
      className={`bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-1 px-3 rounded text-sm ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      disabled={loading}
      >
      Edit
      </button>
      <button
      onClick={() => handleDelete(todo.id)}
      className={`bg-red-500 hover:bg-red-600 text-white font-bold py-1 px-3 rounded text-sm ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      disabled={loading}
      >
      Delete
      </button>
      </div>
      </li>
    ))}
    </ul>
    </div>
  );
}

export default App;
