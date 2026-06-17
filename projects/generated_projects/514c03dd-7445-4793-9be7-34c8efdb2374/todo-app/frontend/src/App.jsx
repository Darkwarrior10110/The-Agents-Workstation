import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000'; // FastAPI backend runs on port 8000

function App() {
    const [todos, setTodos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [newTodoTitle, setNewTodoTitle] = useState('');
    const [newTodoDescription, setNewTodoDescription] = useState('');
    const [editingTodo, setEditingTodo] = useState(null); // Stores the todo being edited

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
            console.error("Failed to fetch todos:", err);
            setError('Failed to load todos. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTodos();
    }, []);

    const handleAddTodo = async (e) => {
        e.preventDefault();
        if (!newTodoTitle.trim()) {
            alert('Todo title cannot be empty.');
            return;
        }

        setLoading(true); // Indicate loading for the specific action
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/todos/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: newTodoTitle.trim(),
                    description: newTodoDescription.trim() || null,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const newTodo = await response.json();
            setTodos((prevTodos) => [...prevTodos, newTodo]);
            setNewTodoTitle('');
            setNewTodoDescription('');
        } catch (err) {
            console.error("Failed to add todo:", err);
            setError(`Failed to add todo: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleComplete = async (id, currentCompletedStatus) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/todos/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    completed: !currentCompletedStatus,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const updatedTodo = await response.json();
            setTodos((prevTodos) =>
                prevTodos.map((todo) => (todo.id === id ? updatedTodo : todo))
            );
        } catch (err) {
            console.error("Failed to update todo status:", err);
            setError(`Failed to update todo status: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteTodo = async (id) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/todos/${id}`, {
                method: 'DELETE',
            });

            if (response.status === 404) {
                throw new Error("Todo not found.");
            } else if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            setTodos((prevTodos) => prevTodos.filter((todo) => todo.id !== id));
        } catch (err) {
            console.error("Failed to delete todo:", err);
            setError(`Failed to delete todo: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleEditClick = (todo) => {
        setEditingTodo({ ...todo }); // Create a copy to edit
    };

    const handleUpdateTodo = async (e) => {
        e.preventDefault();
        if (!editingTodo.title.trim()) {
            alert('Todo title cannot be empty.');
            return;
        }

        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/todos/${editingTodo.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: editingTodo.title.trim(),
                    description: editingTodo.description?.trim() || null,
                    completed: editingTodo.completed,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const updatedTodo = await response.json();
            setTodos((prevTodos) =>
                prevTodos.map((todo) => (todo.id === updatedTodo.id ? updatedTodo : todo))
            );
            setEditingTodo(null); // Exit edit mode
        } catch (err) {
            console.error("Failed to update todo:", err);
            setError(`Failed to update todo: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString();
    };

    return (
        <div className="min-h-screen bg-gray-100 p-4 font-sans">
            <div className="max-w-xl mx-auto bg-white shadow-lg rounded-lg p-6 space-y-6">
                <h1 className="text-4xl font-extrabold text-center text-gray-800 mb-8">Todo App</h1>

                {/* Add New Todo Form */}
                <form onSubmit={handleAddTodo} className="flex flex-col gap-4 p-4 border border-gray-200 rounded-md bg-gray-50">
                    <h2 className="text-2xl font-semibold text-gray-700">Add a New Todo</h2>
                    <input
                        type="text"
                        placeholder="Todo Title (e.g., Buy groceries)"
                        value={newTodoTitle}
                        onChange={(e) => setNewTodoTitle(e.target.value)}
                        className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={loading}
                        required
                    />
                    <textarea
                        placeholder="Description (optional)"
                        value={newTodoDescription}
                        onChange={(e) => setNewTodoDescription(e.target.value)}
                        className="p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-24 resize-none"
                        disabled={loading}
                    ></textarea>
                    <button
                        type="submit"
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={loading}
                    >
                        {loading && !editingTodo ? 'Adding Todo...' : 'Add Todo'}
                    </button>
                </form>

                {/* Loading and Error Messages */}
                {loading && <p className="text-center text-blue-600 font-medium">Loading todos...</p>}
                {error && <p className="text-center text-red-600 font-medium">Error: {error}</p>}

                {/* Todos List */}
                <div className="space-y-4">
                    <h2 className="text-2xl font-semibold text-gray-700">Your Todos</h2>
                    {todos.length === 0 && !loading && !error ? (
                        <p className="text-center text-gray-500">No todos found. Add one above!</p>
                    ) : (
                        todos.map((todo) => (
                            <div
                                key={todo.id}
                                className={`p-4 border rounded-md shadow-sm ${todo.completed ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'}`}
                            >
                                {editingTodo && editingTodo.id === todo.id ? (
                                    <form onSubmit={handleUpdateTodo} className="flex flex-col gap-3">
                                        <input
                                            type="text"
                                            value={editingTodo.title}
                                            onChange={(e) => setEditingTodo({ ...editingTodo, title: e.target.value })}
                                            className="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-400 text-lg font-semibold"
                                            disabled={loading}
                                            required
                                        />
                                        <textarea
                                            value={editingTodo.description || ''}
                                            onChange={(e) => setEditingTodo({ ...editingTodo, description: e.target.value })}
                                            className="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-400 text-sm resize-none h-20"
                                            disabled={loading}
                                        ></textarea>
                                        <label className="flex items-center space-x-2 text-gray-700">
                                            <input
                                                type="checkbox"
                                                checked={editingTodo.completed}
                                                onChange={(e) => setEditingTodo({ ...editingTodo, completed: e.target.checked })}
                                                className="form-checkbox h-5 w-5 text-blue-600 rounded focus:ring-blue-500"
                                                disabled={loading}
                                            />
                                            <span>Completed</span>
                                        </label>
                                        <div className="flex gap-2 mt-2">
                                            <button
                                                type="submit"
                                                className="flex-1 bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-3 rounded-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                                disabled={loading}
                                            >
                                                {loading ? 'Saving...' : 'Save'}
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setEditingTodo(null)}
                                                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 font-semibold py-2 px-3 rounded-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                                disabled={loading}
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </form>
                                ) : (
                                    <div>
                                        <div className="flex items-center justify-between">
                                            <h3 className={`text-lg font-semibold ${todo.completed ? 'line-through text-gray-500' : 'text-gray-800'}`}>
                                                {todo.title}
                                            </h3>
                                            <span className={`text-sm font-medium ${todo.completed ? 'text-green-600' : 'text-red-500'}`}>
                                                {todo.completed ? 'Completed' : 'Pending'}
                                            </span>
                                        </div>
                                        {todo.description && (
                                            <p className="text-gray-600 text-sm mt-1 mb-2">
                                                {todo.description}
                                            </p>
                                        )}
                                        <p className="text-xs text-gray-400 mt-2">Created: {formatDate(todo.created_at)}</p>
                                        <div className="flex gap-2 mt-4">
                                            <button
                                                onClick={() => handleToggleComplete(todo.id, todo.completed)}
                                                className={`flex-1 ${todo.completed ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-green-500 hover:bg-green-600'} text-white font-semibold py-2 px-3 rounded-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed`}
                                                disabled={loading}
                                            >
                                                {todo.completed ? 'Mark as Pending' : 'Mark as Complete'}
                                            </button>
                                            <button
                                                onClick={() => handleEditClick(todo)}
                                                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-3 rounded-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                                disabled={loading}
                                            >
                                                Edit
                                            </button>
                                            <button
                                                onClick={() => handleDeleteTodo(todo.id)}
                                                className="flex-1 bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-3 rounded-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                                disabled={loading}
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}

export default App;
