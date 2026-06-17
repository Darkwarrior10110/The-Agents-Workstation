import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // FastAPI backend runs on port 8000

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Health Check (optional, but good practice)
export const getHealthStatus = async () => {
    try {
        const response = await api.get('/health');
        return response.data;
    } catch (error) {
        console.error('Error fetching health status:', error);
        throw error; // Re-throw to be handled by calling component
    }
};

// Todos API Calls

/**
 * Fetches all Todos from the backend.
 * @returns {Promise<Array<Object>>} A promise that resolves to an array of todo objects.
 */
export const getTodos = async () => {
    try {
        const response = await api.get('/todos');
        return response.data;
    } catch (error) {
        console.error('Error fetching todos:', error);
        throw error;
    }
};

/**
 * Fetches a single Todo by its ID.
 * @param {string} id - The ID of the todo to fetch.
 * @returns {Promise<Object>} A promise that resolves to a single todo object.
 */
export const getTodoById = async (id) => {
    try {
        const response = await api.get(`/todos/${id}`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching todo with ID ${id}:`, error);
        throw error;
    }
};

/**
 * Creates a new Todo.
 * @param {Object} todoData - The data for the new todo (title, description, completed).
 * @returns {Promise<Object>} A promise that resolves to the newly created todo object.
 */
export const createTodo = async (todoData) => {
    try {
        const response = await api.post('/todos', todoData);
        return response.data;
    } catch (error) {
        console.error('Error creating todo:', error);
        throw error;
    }
};

/**
 * Updates an existing Todo.
 * @param {string} id - The ID of the todo to update.
 * @param {Object} todoData - The data to update the todo with (title, description, completed).
 * @returns {Promise<Object>} A promise that resolves to the updated todo object.
 */
export const updateTodo = async (id, todoData) => {
    try {
        const response = await api.put(`/todos/${id}`, todoData);
        return response.data;
    } catch (error) {
        console.error(`Error updating todo with ID ${id}:`, error);
        throw error;
    }
};

/**
 * Deletes a Todo by its ID.
 * @param {string} id - The ID of the todo to delete.
 * @returns {Promise<void>} A promise that resolves when the todo is successfully deleted.
 */
export const deleteTodo = async (id) => {
    try {
        await api.delete(`/todos/${id}`);
    } catch (error) {
        console.error(`Error deleting todo with ID ${id}:`, error);
        throw error;
    }
};
