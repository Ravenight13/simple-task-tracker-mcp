// API Configuration
// This file contains the API endpoint and key configuration

const API_CONFIG = {
  // API base URL (update for production)
  baseUrl: 'http://localhost:8001/api',

  // API key (stored in localStorage, or set here for development)
  // For production, prompt user to enter API key on first visit
  getApiKey: () => {
    return localStorage.getItem('task_viewer_api_key') || '';
  },

  // Save API key to localStorage
  setApiKey: (key) => {
    localStorage.setItem('task_viewer_api_key', key);
  },

  // Clear API key
  clearApiKey: () => {
    localStorage.removeItem('task_viewer_api_key');
  }
};
