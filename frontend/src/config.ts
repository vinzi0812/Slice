/**
 * API Configuration
 * Centralized API endpoint configuration for the frontend
 */

// Backend API base URL
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: `${API_BASE_URL}/api/auth/login`,
    LOGOUT: `${API_BASE_URL}/api/auth/logout`,
    GOOGLE_LOGIN: `${API_BASE_URL}/api/auth/google/login`,
    ME: `${API_BASE_URL}/api/auth/me`,
  },

  // Users
  USERS: {
    LIST: `${API_BASE_URL}/api/users/`,
    GET: (id: number) => `${API_BASE_URL}/api/users/${id}`,
  },

  // Groups
  GROUPS: {
    LIST: `${API_BASE_URL}/api/groups/`,
    CREATE: `${API_BASE_URL}/api/groups/`,
    GET: (id: number) => `${API_BASE_URL}/api/groups/${id}`,
  },

  // Expenses
  EXPENSES: {
    LIST: `${API_BASE_URL}/api/expenses/`,
    CREATE: `${API_BASE_URL}/api/expenses/`,
    GET: (id: number) => `${API_BASE_URL}/api/expenses/${id}`,
    GROUP: (groupId: number) => `${API_BASE_URL}/api/expenses/group/${groupId}`,
  },

  // Settlements
  SETTLEMENTS: {
    CREATE: `${API_BASE_URL}/api/settlements/`,
    GROUP: (groupId: number) => `${API_BASE_URL}/api/settlements/group/${groupId}`,
  },
};

export default API_ENDPOINTS;
