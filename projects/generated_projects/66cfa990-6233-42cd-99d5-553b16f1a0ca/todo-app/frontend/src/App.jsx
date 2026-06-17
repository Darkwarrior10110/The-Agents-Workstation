import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newTodoTitle, setNewTodoTitle] = useState('');
  const [newTodoDescription, setNewTodoDescription] = useState('');
  const [editingTodo, setEditingTodo] = useState(null); // Stores the todo being edited

  useEffect(() => {
    fetchTodos();
  }, []);

  const fetchTodos = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/todos`);
      setTodos(response.data);
    } catch (err) {
      console.error("Error fetching todos:", err);
      setError('Failed to fetch todos. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddOrUpdateTodo = async (e) => {
    e.preventDefault();
    setError(null);

    if (!newTodoTitle.trim()) {
      setError('Todo title cannot be empty.');
      return;
    }

    try {
      if (editingTodo) {
        // Update existing todo
        const updatedTodoData = {
          title: newTodoTitle,
          description: newTodoDescription,
        };
        const response = await axios.put(`${API_BASE_URL}/todos/${editingTodo.id}`, updatedTodoData);
        setTodos(todos.map((todo) => (todo.id === editingTodo.id ? response.data : todo)));
        setEditingTodo(null);
      } else {
        // Add new todo
        const newTodoData = {
          title: newTodoTitle,
          description: newTodoDescription,
        };
        const response = await axios.post(`${API_BASE_URL}/todos`, newTodoData);
        setTodos([...todos, response.data]);
      }
      setNewTodoTitle('');
      setNewTodoDescription('');
    } catch (err) {
      console.error('Error saving todo:', err);
      setError('Failed to save todo. Please check your input and try again.');
    }
  };

  const handleToggleComplete = async (id, completed) => {
    setError(null);
    try {
      const response = await axios.put(`${API_BASE_URL}/todos/${id}`, { completed: !completed });
      setTodos(todos.map((todo) => (todo.id === id ? response.data : todo)));
    } catch (err) {
      console.error('Error toggling todo completion:', err);
      setError('Failed to update todo status. Please try again.');
    }
  };

  const handleDeleteTodo = async (id) => {
    setError(null);
    if (!window.confirm('Are you sure you want to delete this todo?')) {
      return;
    }
    try {
      await axios.delete(`${API_BASE_URL}/todos/${id}`);
      setTodos(todos.filter((todo) => todo.id !== id));
    } catch (err) {
      console.error('Error deleting todo:', err);
      setError('Failed to delete todo. Please try again.');
    }
  };

  const startEditing = (todo) => {
    setEditingTodo(todo);
    setNewTodoTitle(todo.title);
    setNewTodoDescription(todo.description || '');
  };

  const cancelEditing = () => {
    setEditingTodo(null);
    setNewTodoTitle('');
    setNewTodoDescription('');
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="container mx-auto max-w-2xl bg-white shadow-lg rounded-lg p-6 mt-8">
        <h1 className="text-4xl font-extrabold text-center text-indigo-700 mb-8">Todo App</h1>

        {/* Todo Form */}
        <form onSubmit={handleAddOrUpdateTodo} className="mb-8 p-6 bg-indigo-50 rounded-lg shadow-md">
          <h2 className="text-2xl font-semibold text-indigo-800 mb-4">
            {editingTodo ? 'Edit Todo' : 'Add New Todo'}
          </h2>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
              <span className="block sm:inline">{error}</span>
            </div>
          )}
          <div className="mb-4">
            <label htmlFor="title" className="block text-gray-700 text-sm font-bold mb-2">Title:</label>
            <input
              type="text"
              id="title"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:border-indigo-500"
              value={newTodoTitle}
              onChange={(e) => setNewTodoTitle(e.target.value)}
              placeholder="What needs to be done?"
              required
            />
          </div>
          <div className="mb-6">
            <label htmlFor="description" className="block text-gray-700 text-sm font-bold mb-2">Description (Optional):</label>
            <textarea
              id="description"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline focus:border-indigo-500 h-24 resize-none"
              value={newTodoDescription}
              onChange={(e) => setNewTodoDescription(e.target.value)}
              placeholder="Add a description..."
            />
          </div>
          <div className="flex items-center justify-between">
            <button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200"
            >
              {editingTodo ? 'Update Todo' : 'Add Todo'}
            </button>
            {editingTodo && (
              <button
                type="button"
                onClick={cancelEditing}
                className="ml-4 bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-200"
              >
                Cancel
              </button>
            )}
          </div>
        </form>

        {/* Todo List */}
        <h2 className="text-3xl font-bold text-center text-indigo-700 mb-6">My Todos</h2>
        {loading ? (
          <p className="text-center text-gray-500 text-lg">Loading todos...</p>
        ) : todos.length === 0 ? (
          <p className="text-center text-gray-500 text-lg">No todos yet. Add one above!</p>
        ) : (
          <ul className="space-y-4">
            {todos.map((todo) => (
              <li
                key={todo.id}
                className={`flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 border rounded-lg shadow-sm transition duration-200 ${todo.completed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}
              >
                <div className="flex-1 min-w-0 mr-4">
                  <div className="flex items-center mb-2 sm:mb-0">
                    <input
                      type="checkbox"
                      className="mr-3 h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      checked={todo.completed}
                      onChange={() => handleToggleComplete(todo.id, todo.completed)}
                    />
                    <span className={`text-lg font-medium ${todo.completed ? 'line-through text-gray-500' : 'text-gray-800'}`}>
                      {todo.title}
                    </span>
                  </div>
                  {todo.description && (
                    <p className={`text-sm text-gray-600 ml-8 mt-1 ${todo.completed ? 'line-through' : ''}`}>
                      {todo.description}
                    </p>
                  )}
                  <p className="text-xs text-gray-400 ml-8 mt-1">Created: {new Date(todo.created_at).toLocaleString()}</p>
                  <p className="text-xs text-gray-400 ml-8">Updated: {new Date(todo.updated_at).toLocaleString()}</p>
                </div>
                <div className="flex-shrink-0 mt-3 sm:mt-0 flex space-x-2">
                  <button
                    onClick={() => startEditing(todo)}
                    className="bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium py-1 px-3 rounded transition duration-200"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteTodo(todo.id)}
                    className="bg-red-500 hover:bg-red-600 text-white text-sm font-medium py-1 px-3 rounded transition duration-200"
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default App;
