const BASE_URL = 'http://localhost:8000';

const handleResponse = async (response) => {
  if (!response.ok) {
    let errorMessage = `HTTP error! status: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage; // FastAPI often puts error details in 'detail'
    } catch (e) {
      // If response is not JSON, use the status text
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  // For 204 No Content responses, return null as there's no body to parse
  if (response.status === 204) {
    return null;
  }
  return response.json();
};

export const getHealth = async () => {
  try {
    const response = await fetch(`${BASE_URL}/health`);
    return handleResponse(response);
  } catch (error) {
    console.error('Error fetching health status:', error);
    throw error;
  }
};

export const getTodos = async () => {
  try {
    const response = await fetch(`${BASE_URL}/todos`);
    return handleResponse(response);
  } catch (error) {
    console.error('Error fetching todos:', error);
    throw error;
  }
};

export const createTodo = async (todoData) => {
  try {
    const response = await fetch(`${BASE_URL}/todos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(todoData),
    });
    return handleResponse(response);
  } catch (error) {
    console.error('Error creating todo:', error);
    throw error;
  }
};

export const updateTodo = async (id, updateData) => {
  try {
    const response = await fetch(`${BASE_URL}/todos/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateData),
    });
    return handleResponse(response);
  } catch (error) {
    console.error(`Error updating todo ${id}:`, error);
    throw error;
  }
};

export const deleteTodo = async (id) => {
  try {
    const response = await fetch(`${BASE_URL}/todos/${id}`, {
      method: 'DELETE',
    });
    return handleResponse(response); // 204 No Content, will return null
  } catch (error) {
    console.error(`Error deleting todo ${id}:`, error);
    throw error;
  }
};
