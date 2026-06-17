const BASE_URL = 'http://localhost:8000';

const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  // For DELETE (204 No Content), response.json() would throw an error
  if (response.status === 204) {
    return null; 
  }
  return response.json();
};

export const getTodos = async () => {
  try {
    const response = await fetch(`${BASE_URL}/todos/`);
    return handleResponse(response);
  } catch (error) {
    console.error('Error fetching todos:', error);
    throw error;
  }
};

export const getTodoById = async (id) => {
  try {
    const response = await fetch(`${BASE_URL}/todos/${id}`);
    return handleResponse(response);
  } catch (error) {
    console.error(`Error fetching todo with ID ${id}:`, error);
    throw error;
  }
};

export const createTodo = async (todo) => {
  try {
    const response = await fetch(`${BASE_URL}/todos/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(todo),
    });
    return handleResponse(response);
  } catch (error) {
    console.error('Error creating todo:', error);
    throw error;
  }
};

export const updateTodo = async (id, todo) => {
  try {
    const response = await fetch(`${BASE_URL}/todos/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(todo),
    });
    return handleResponse(response);
  } catch (error) {
    console.error(`Error updating todo with ID ${id}:`, error);
    throw error;
  }
};

export const deleteTodo = async (id) => {
  try {
    const response = await fetch(`${BASE_URL}/todos/${id}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  } catch (error) {
    console.error(`Error deleting todo with ID ${id}:`, error);
    throw error;
  }
};

export const getHealthStatus = async () => {
  try {
    const response = await fetch(`${BASE_URL}/health`);
    return handleResponse(response);
  } catch (error) {
    console.error('Error fetching health status:', error);
    throw error;
  }
};
