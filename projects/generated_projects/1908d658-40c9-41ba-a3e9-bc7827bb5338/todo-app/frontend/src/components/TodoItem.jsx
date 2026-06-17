import React from 'react';

const TodoItem = ({ todo, onToggleComplete, onDelete }) => {
  const { id, title, description, completed, created_at } = todo;

  const handleToggle = () => {
    onToggleComplete(id);
  };

  const handleDelete = () => {
    onDelete(id);
  };

  const formattedDate = created_at ? new Date(created_at).toLocaleString() : '';

  return (
    <div className={`
      flex items-center justify-between p-4 rounded-lg shadow-md mb-4
      ${completed ? 'bg-gray-100 dark:bg-gray-700' : 'bg-white dark:bg-gray-800'}
    `}>
      <div className="flex items-center flex-grow">
        <input
          type="checkbox"
          checked={completed}
          onChange={handleToggle}
          className="mr-3 h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 dark:bg-gray-600 dark:border-gray-500 dark:focus:ring-indigo-600 cursor-pointer"
          aria-label={`Mark "${title}" as ${completed ? 'incomplete' : 'complete'}`}
        />
        <div className="flex-grow min-w-0">
          <h3 className={`font-bold text-lg ${completed ? 'line-through text-gray-500 dark:text-gray-400' : 'text-gray-900 dark:text-white'} break-words`}>
            {title}
          </h3>
          {description && (
            <p className={`text-sm mt-1 ${completed ? 'line-through text-gray-400 dark:text-gray-500' : 'text-gray-600 dark:text-gray-300'} break-words`}>
              {description}
            </p>
          )}
          {formattedDate && (
            <p className="text-xs text-gray-400 mt-1 dark:text-gray-500">
              Created: {formattedDate}
            </p>
          )}
        </div>
      </div>
      <button
        onClick={handleDelete}
        className="ml-4 px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50 transition duration-150 ease-in-out flex-shrink-0"
        aria-label={`Delete todo: ${title}`}
      >
        Delete
      </button>
    </div>
  );
};

export default TodoItem;
