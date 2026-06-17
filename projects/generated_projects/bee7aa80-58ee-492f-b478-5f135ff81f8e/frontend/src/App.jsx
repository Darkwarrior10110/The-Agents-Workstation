import React, { useState, useEffect } from 'react';
import { getTodos, createTodo, updateTodo, deleteTodo, getHealthStatus } from './api';

function App() {
    const [todos, setTodos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [newTodoTitle, setNewTodoTitle] = useState('');
    const [newTodoDescription, setNewTodoDescription] = useState('');
    const [editingTodoId, setEditingTodoId] = useState(null);
    const [editingTodoTitle, setEditingTodoTitle] = useState('');
    const [editingTodoDescription, setEditingTodoDescription] = useState('');
    const [editingTodoCompleted, setEditingTodoCompleted] = useState(false);

    useEffect(() => {
        fetchTodos();
        checkBackendHealth(); // Optional: Check backend health on startup
    }, []);

    const checkBackendHealth = async () => {
        try {
            await getHealthStatus();
            // console.log("Backend is healthy!");
        } catch (err) {
            setError("Backend API is unreachable. Please ensure the backend server is running.");
        }
    };

    const fetchTodos = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getTodos();
            setTodos(data);
        } catch (err) {
            setError('Failed to fetch todos.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleAddTodo = async (e) => {
        e.preventDefault();
        if (!newTodoTitle.trim()) {
            setError('Todo title cannot be empty.');
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const newTodo = await createTodo({
                title: newTodoTitle,
                description: newTodoDescription,
            });
            setTodos((prevTodos) => [...prevTodos, newTodo]);
            setNewTodoTitle('');
            setNewTodoDescription('');
        } catch (err) {
            setError('Failed to create todo.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleEditClick = (todo) => {
        setEditingTodoId(todo.id);
        setEditingTodoTitle(todo.title);
        setEditingTodoDescription(todo.description);
        setEditingTodoCompleted(todo.completed);
    };

    const handleCancelEdit = () => {
        setEditingTodoId(null);
        setEditingTodoTitle('');
        setEditingTodoDescription('');
        setEditingTodoCompleted(false);
    };

    const handleUpdateTodo = async (e) => {
        e.preventDefault();
        if (!editingTodoTitle.trim()) {
            setError('Todo title cannot be empty.');
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const updatedTodo = await updateTodo(editingTodoId, {
                title: editingTodoTitle,
                description: editingTodoDescription,
                completed: editingTodoCompleted,
            });
            setTodos((prevTodos) =>
                prevTodos.map((todo) => (todo.id === editingTodoId ? updatedTodo : todo))
            );
            handleCancelEdit(); // Exit edit mode
        } catch (err) {
            setError('Failed to update todo.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteTodo = async (id) => {
        setLoading(true);
        setError(null);
        try {
            await deleteTodo(id);
            setTodos((prevTodos) => prevTodos.filter((todo) => todo.id !== id));
        } catch (err) {
            setError('Failed to delete todo.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleComplete = async (todo) => {
        setLoading(true);
        setError(null);
        try {
            const updatedTodo = await updateTodo(todo.id, { completed: !todo.completed });
            setTodos((prevTodos) =>
                prevTodos.map((t) => (t.id === todo.id ? updatedTodo : t))
            );
        } catch (err) {
            setError('Failed to toggle todo status.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-500 to-indigo-600 p-8 flex flex-col items-center">
            <h1 className="text-5xl font-extrabold text-white mb-10 drop-shadow-lg">
                My Todo List
            </h1>

            {error && (
                <div className="bg-red-500 text-white p-4 rounded-lg shadow-md mb-6 w-full max-w-2xl text-center">
                    {error}
                </div>
            )}

            {loading && (
                <div className="flex items-center space-x-2 text-white text-lg mb-6">
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Loading...</span>
                </div>
            )}

            {/* Todo Creation Form */}
            <form onSubmit={handleAddTodo} className="bg-white p-8 rounded-xl shadow-2xl mb-10 w-full max-w-2xl transform transition-all hover:scale-105 duration-300">
                <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Add New Todo</h2>
                <div className="mb-4">
                    <label htmlFor="newTodoTitle" className="block text-gray-700 text-sm font-semibold mb-2">Title</label>
                    <input
                        type="text"
                        id="newTodoTitle"
                        className="shadow-sm appearance-none border rounded-lg w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition duration-200"
                        placeholder="e.g., Buy groceries"
                        value={newTodoTitle}
                        onChange={(e) => setNewTodoTitle(e.target.value)}
                        required
                    />
                </div>
                <div className="mb-6">
                    <label htmlFor="newTodoDescription" className="block text-gray-700 text-sm font-semibold mb-2">Description (Optional)</label>
                    <textarea
                        id="newTodoDescription"
                        className="shadow-sm appearance-none border rounded-lg w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition duration-200 resize-y"
                        placeholder="e.g., Milk, eggs, bread, fruits"
                        value={newTodoDescription}
                        onChange={(e) => setNewTodoDescription(e.target.value)}
                        rows="3"
                    ></textarea>
                </div>
                <button
                    type="submit"
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-lg shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-75 transition duration-300 transform hover:-translate-y-0.5"
                    disabled={loading}
                >
                    {loading ? 'Adding...' : 'Add Todo'}
                </button>
            </form>

            {/* Todo List */}
            <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-2xl">
                <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Your Todos</h2>
                {todos.length === 0 && !loading && !error && (
                    <p className="text-gray-600 text-center italic">No todos yet. Add one above!</p>
                )}
                <ul className="space-y-4">
                    {todos.map((todo) => (
                        <li
                            key={todo.id}
                            className={`flex flex-col md:flex-row justify-between items-start md:items-center p-5 rounded-lg shadow-md transition duration-300 ${
                                todo.completed ? 'bg-green-50 border-l-4 border-green-500' : 'bg-gray-50 border-l-4 border-indigo-400'
                            }`}
                        >
                            {editingTodoId === todo.id ? (
                                <form onSubmit={handleUpdateTodo} className="w-full space-y-3">
                                    <div>
                                        <label htmlFor={`editTitle-${todo.id}`} className="sr-only">Title</label>
                                        <input
                                            type="text"
                                            id={`editTitle-${todo.id}`}
                                            className="shadow-sm border rounded-lg w-full py-2 px-3 text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                                            value={editingTodoTitle}
                                            onChange={(e) => setEditingTodoTitle(e.target.value)}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor={`editDescription-${todo.id}`} className="sr-only">Description</label>
                                        <textarea
                                            id={`editDescription-${todo.id}`}
                                            className="shadow-sm border rounded-lg w-full py-2 px-3 text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-y"
                                            value={editingTodoDescription}
                                            onChange={(e) => setEditingTodoDescription(e.target.value)}
                                            rows="2"
                                        ></textarea>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <input
                                            type="checkbox"
                                            id={`editCompleted-${todo.id}`}
                                            className="form-checkbox h-5 w-5 text-indigo-600 rounded-md focus:ring-indigo-500"
                                            checked={editingTodoCompleted}
                                            onChange={(e) => setEditingTodoCompleted(e.target.checked)}
                                        />
                                        <label htmlFor={`editCompleted-${todo.id}`} className="text-gray-700 select-none">Completed</label>
                                    </div>
                                    <div className="flex space-x-2 mt-4">
                                        <button
                                            type="submit"
                                            className="flex-1 bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg shadow-md transition duration-200"
                                            disabled={loading}
                                        >
                                            Save
                                        </button>
                                        <button
                                            type="button"
                                            onClick={handleCancelEdit}
                                            className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded-lg shadow-md transition duration-200"
                                            disabled={loading}
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </form>
                            ) : (
                                <>
                                    <div className="flex-1 min-w-0 pr-4">
                                        <h3 className={`text-xl font-semibold ${todo.completed ? 'text-gray-500 line-through' : 'text-gray-800'}`}>
                                            {todo.title}
                                        </h3>
                                        {todo.description && (
                                            <p className={`text-gray-600 mt-1 ${todo.completed ? 'line-through' : ''}`}>
                                                {todo.description}
                                            </p>
                                        )}
                                        <p className="text-sm text-gray-400 mt-2">
                                            Created: {new Date(todo.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                    <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-2 mt-4 md:mt-0">
                                        <button
                                            onClick={() => handleToggleComplete(todo)}
                                            className={`py-2 px-4 rounded-lg text-sm font-medium transition duration-200 ${
                                                todo.completed
                                                    ? 'bg-yellow-500 hover:bg-yellow-600 text-white shadow-md'
                                                    : 'bg-green-500 hover:bg-green-600 text-white shadow-md'
                                            }`}
                                            disabled={loading}
                                        >
                                            {todo.completed ? 'Mark Incomplete' : 'Mark Complete'}
                                        </button>
                                        <button
                                            onClick={() => handleEditClick(todo)}
                                            className="py-2 px-4 rounded-lg bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium shadow-md transition duration-200"
                                            disabled={loading}
                                        >
                                            Edit
                                        </button>
                                        <button
                                            onClick={() => handleDeleteTodo(todo.id)}
                                            className="py-2 px-4 rounded-lg bg-red-500 hover:bg-red-600 text-white text-sm font-medium shadow-md transition duration-200"
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
        </div>
    );
}

export default App;
