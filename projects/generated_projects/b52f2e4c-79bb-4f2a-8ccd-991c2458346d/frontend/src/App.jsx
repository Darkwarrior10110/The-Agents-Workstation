import React, { useState, useEffect } from 'react';
import { getTodos, createTodo, updateTodo, deleteTodo } from './api';
import TodoList from './components/TodoList'; // Assuming this component exists in ./components
import TodoForm from './components/TodoForm'; // Assuming this component exists in ./components
import './App.css'; // Keeping existing CSS import from snapshot
import './index.css'; // Likely for TailwindCSS base styles

function App() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingTodo, setEditingTodo] = useState(null); // Holds the todo object being edited
  const [isFormVisible, setIsFormVisible] = useState(false); // Controls visibility of the add/edit form

  // Fetch todos on component mount
  useEffect(() => {
    fetchTodos();
  }, []);

  const fetchTodos = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTodos();
      setTodos(data);
    } catch (err) {
      console.error('Error fetching todos:', err);
      setError('Failed to fetch todos. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const addTodo = async (newTodo) => {
    setLoading(true);
    setError(null);
    try {
      const created = await createTodo(newTodo);
      setTodos((prevTodos) => [...prevTodos, created]);
      setIsFormVisible(false); // Hide form after successful addition
    } catch (err) {
      console.error('Error adding todo:', err);
      setError('Failed to add todo. ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateTodoHandler = async (id, updatedFields) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await updateTodo(id, updatedFields);
      setTodos((prevTodos) =>
        prevTodos.map((todo) => (todo.id === id ? updated : todo))
      );
      setEditingTodo(null); // Clear editing state
      setIsFormVisible(false); // Hide form after successful update
    } catch (err) {
      console.error('Error updating todo:', err);
      setError('Failed to update todo. ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteTodoHandler = async (id) => {
    setLoading(true);
    setError(null);
    try {
      await deleteTodo(id);
      setTodos((prevTodos) => prevTodos.filter((todo) => todo.id !== id));
    } catch (err) {
      console.error('Error deleting todo:', err);
      setError('Failed to delete todo. ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleComplete = async (id, currentCompletedStatus) => {
    // Optimistic update
    setTodos((prevTodos) =>
      prevTodos.map((todo) =>
        todo.id === id ? { ...todo, completed: !currentCompletedStatus } : todo
      )
    );
    setError(null);
    try {
      await updateTodo(id, { completed: !currentCompletedStatus });
    } catch (err) {
      console.error('Error toggling todo completion:', err);
      setError('Failed to toggle todo completion. ' + err.message);
      // Revert optimistic update on error
      setTodos((prevTodos) =>
        prevTodos.map((todo) =>
          todo.id === id ? { ...todo, completed: currentCompletedStatus } : todo
        )
      );
    }
  };

  const startEditing = (todo) => {
    setEditingTodo(todo);
    setIsFormVisible(true); // Show the form for editing
  };

  const cancelEditing = () => {
    setEditingTodo(null);
    setIsFormVisible(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-4 font-sans">
      <h1 className="text-5xl font-extrabold text-indigo-700 mt-8 mb-12 drop-shadow-lg text-center">
        My Todo App
      </h1>

      <div className="w-full max-w-2xl bg-white shadow-xl rounded-lg p-6 space-y-6">
        {/* Conditional rendering of TodoForm or Add New Todo Button */}
        {(isFormVisible || editingTodo) ? (
          <TodoForm
            onSubmit={editingTodo ? updateTodoHandler : addTodo}
            initialTodo={editingTodo}
            onCancelEdit={cancelEditing}
            isEditing={!!editingTodo}
          />
        ) : (
          <button
            onClick={() => setIsFormVisible(true)}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-50"
          >
            Add New Todo
          </button>
        )}

        {/* Loading and Error states */}
        {loading && (
          <div className="text-center text-gray-600 text-lg py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-500 inline-block mr-2"></div>
            Loading todos...
          </div>
        )}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative text-center" role="alert">
            <span className="block sm:inline">Error: {error}</span>
          </div>
        )}

        {/* Todo List */}
        {!loading && !error && (
          <TodoList
            todos={todos}
            onToggleComplete={toggleComplete}
            onDelete={deleteTodoHandler}
            onEdit={startEditing}
          />
        )}
      </div>
    </div>
  );
}

export default App;
