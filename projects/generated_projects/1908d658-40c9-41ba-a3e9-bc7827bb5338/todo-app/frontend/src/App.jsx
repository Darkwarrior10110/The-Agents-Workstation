import React, { useState, useEffect, useCallback } from 'react';
import AddTodoForm from './components/AddTodoForm';
import TodoList from './components/TodoList';
import { getTodos, createTodo, updateTodo, deleteTodo, getHealth } from './api';

const App = () => {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true); // For initial fetch of todos
  const [error, setError] = useState(null); // General error for fetching/other ops
  const [addTodoLoading, setAddTodoLoading] = useState(false); // For adding a new todo
  const [addTodoError, setAddTodoError] = useState(null); // Error specific to adding a todo
  const [healthStatus, setHealthStatus] = useState(null);

  // Function to fetch all todos
  const fetchTodos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const fetchedTodos = await getTodos();
      setTodos(fetchedTodos);
    } catch (err) {
      console.error('Failed to fetch todos:', err);
      setError(err.message || 'Failed to load todos.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Function to check backend health
  const checkHealth = useCallback(async () => {
    try {
      const status = await getHealth();
      setHealthStatus(status.status === 'ok');
    } catch (err) {
      console.error('Backend health check failed:', err);
      setHealthStatus(false);
    }
  }, []);

  // Initial data fetch and health check on component mount
  useEffect(() => {
    fetchTodos();
    checkHealth();
    // Optionally, re-check health periodically or on focus
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [fetchTodos, checkHealth]);

  // Handle adding a new todo
  const handleAddTodo = async (todoData) => {
    setAddTodoLoading(true);
    setAddTodoError(null);
    try {
      const newTodo = await createTodo(todoData);
      setTodos((prevTodos) => [...prevTodos, newTodo].sort((a, b) => new Date(a.created_at) - new Date(b.created_at)));
      setAddTodoLoading(false);
    } catch (err) {
      console.error('Failed to add todo:', err);
      setAddTodoError(err.message || 'Failed to add todo.');
      setAddTodoLoading(false);
    }
  };

  // Handle toggling todo completion status
  const handleToggleComplete = async (id) => {
    const todoToUpdate = todos.find((todo) => todo.id === id);
    if (!todoToUpdate) return;

    const updatedCompletedStatus = !todoToUpdate.completed;
    const originalTodos = todos; // Store original state for potential revert

    // Optimistically update UI
    setTodos((prevTodos) =>
      prevTodos.map((todo) =>
        todo.id === id ? { ...todo, completed: updatedCompletedStatus } : todo
      )
    );

    try {
      await updateTodo(id, { completed: updatedCompletedStatus });
    } catch (err) {
      console.error(`Failed to update todo ${id}:`, err);
      setError(err.message || `Failed to update todo: ${todoToUpdate.title}`);
      setTodos(originalTodos); // Revert UI on error
      // Re-fetch to ensure data consistency in case optimistic update was wrong
      fetchTodos();
    }
  };

  // Handle deleting a todo
  const handleDeleteTodo = async (id) => {
    const todoToDelete = todos.find((todo) => todo.id === id);
    if (!todoToDelete) return;

    const originalTodos = todos; // Store original state for potential revert

    // Optimistically update UI
    setTodos((prevTodos) => prevTodos.filter((todo) => todo.id !== id));

    try {
      await deleteTodo(id);
    } catch (err) {
      console.error(`Failed to delete todo ${id}:`, err);
      setError(err.message || `Failed to delete todo: ${todoToDelete.title}`);
      setTodos(originalTodos); // Revert UI on error
      // Re-fetch to ensure data consistency in case optimistic update was wrong
      fetchTodos();
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center py-10 px-4 bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      <div className="max-w-xl w-full">
        <h1 className="text-4xl font-extrabold text-center text-gray-900 dark:text-white mb-8">
          Todo Application
        </h1>

        {/* Backend Health Status */}
        <div className={`mb-6 p-3 rounded-lg text-sm text-center font-medium ${healthStatus === true ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'}`}>
          Backend Status: {healthStatus === true ? 'Connected' : 'Disconnected'} {healthStatus === false && '- Please ensure backend is running on http://localhost:8000'}
        </div>

        {/* Global Error Display */}
        {error && (
          <div className="p-4 mb-6 bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-300 rounded-lg shadow-md">
            <p className="font-bold text-lg mb-2">Application Error:</p>
            <p>{error}</p>
            <p className="text-sm mt-2">Some operations might not work as expected. Please try again.</p>
            <button
              onClick={() => setError(null)}
              className="mt-3 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50"
            >Clear Error</button>
          </div>
        )}

        <AddTodoForm
          onAddTodo={handleAddTodo}
          loading={addTodoLoading}
          error={addTodoError}
        />

        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6 mt-10 text-center">
          My Todos
        </h2>

        <TodoList
          todos={todos}
          onToggleComplete={handleToggleComplete}
          onDelete={handleDeleteTodo}
          loading={loading}
          error={error} // Pass general error to TodoList for initial fetch errors
        />
      </div>
    </div>
  );
};

export default App;
